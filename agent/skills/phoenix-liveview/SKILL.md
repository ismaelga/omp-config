---
name: phoenix-liveview
description: "Phoenix web layer on the BEAM: LiveView lifecycle and streams, HEEx, LiveComponents, PubSub fan-out, Channels and Presence, LiveViewTest, releases and clustering. Use when writing or reviewing Phoenix/LiveView code, not when designing the domain."
disable-model-invocation: true
---

# Phoenix + LiveView

The web layer. Domain design, supervision-tree planning, Ash resources, ADRs and project
documentation belong to `elixir-architect`; this skill starts where a request arrives and
ends where it leaves.

Two rules the rest of the file assumes:

- **LiveViews stay thin.** State transitions and queries live in contexts. A LiveView
  binds events to context calls and renders assigns.
- **Assigns are a diff budget.** Everything in `socket.assigns` is retained per connected
  client and re-diffed on every update. Large lists belong in a stream, expensive derived
  data behind `assign_new/3`, transient data nowhere.

## Lifecycle

`mount/3` runs twice: once for the static HTTP render, once for the WebSocket connect.
Guard anything stateful with `connected?/1` or it fires twice and leaks on the dead render.

```elixir
defmodule MyAppWeb.OrdersLive do
  use MyAppWeb, :live_view

  @impl true
  def mount(_params, _session, socket) do
    if connected?(socket), do: Phoenix.PubSub.subscribe(MyApp.PubSub, "orders")

    {:ok,
     socket
     |> assign(:filter, :all)
     |> stream(:orders, Orders.list_orders())}
  end

  # URL-driven state lands here, not in mount: handle_params/3 runs on every
  # live_patch and on the initial load, so back/forward buttons keep working.
  @impl true
  def handle_params(%{"filter" => filter}, _uri, socket) do
    {:noreply, assign(socket, :filter, String.to_existing_atom(filter))}
  end

  def handle_params(_params, _uri, socket), do: {:noreply, socket}

  @impl true
  def handle_event("archive", %{"id" => id}, socket) do
    order = Orders.get_order!(id)
    {:ok, _} = Orders.archive_order(order)
    {:noreply, stream_delete(socket, :orders, order)}
  end
end
```

`assign_new/3` computes once per connected session and is inherited by LiveComponents, so
it is the right home for the current user or anything else derived from the session:

```elixir
socket = assign_new(socket, :current_user, fn -> Accounts.get_user!(user_id) end)
```

## Streams, not list assigns

A list in assigns is re-sent in full on every change. `stream/3` sends one DOM operation
per changed item and keeps nothing server-side, which is what makes a live-updating
collection cheap. Prepend with `at: 0`.

```elixir
@impl true
def handle_info({:order_created, order}, socket) do
  {:noreply, stream_insert(socket, :orders, order, at: 0)}
end
```

```heex
<div id="orders" phx-update="stream">
  <div :for={{dom_id, order} <- @streams.orders} id={dom_id}>
    {order.reference} — {order.total}
    <button phx-click="archive" phx-value-id={order.id}>Archive</button>
  </div>
</div>
```

The container needs `phx-update="stream"` and every child needs the stream's `dom_id`, or
the diff has nothing to target. `stream_delete/3` removes by struct, `stream/4` with
`reset: true` replaces the whole collection (use it when a filter changes).

## HEEx

- `{...}` is the interpolation form, in bodies and in attributes: `<p>{@name}</p>`,
  `<div class={@class}>`. `<%= ... %>` is only for block constructs (`if`, `case`, `for`)
  and is not needed for values. Curly braces do not work inside `<script>`/`<style>`.
- `:for` and `:if` are special attributes on any tag or component, and read better than a
  wrapping comprehension: `<li :for={item <- @items} :if={item.visible}>`.
- Routes are verified at compile time with `~p`: `<.link navigate={~p"/orders/#{order}"}>`.
  A typo is a compile error. Never hand-build paths, and never reach for the removed
  `Routes.*_path` helpers.
- `navigate` remounts the LiveView, `patch` reuses the mounted process and re-runs
  `handle_params/3`. Patch within a LiveView, navigate between them.

## LiveComponents

Stateful components get their own `handle_event/3` and their own assigns, addressed by
`id`. Use one when a piece of UI owns interaction state; use a plain function component
for everything else, because a function component costs nothing.

```elixir
defmodule MyAppWeb.FilterComponent do
  use MyAppWeb, :live_component

  @impl true
  def handle_event("select", %{"value" => value}, socket) do
    send(self(), {:filter_changed, value})
    {:noreply, socket}
  end

  @impl true
  def render(assigns) do
    ~H"""
    <form phx-change="select" phx-target={@myself}>
      <select name="value">
        <option :for={opt <- @options} value={opt} selected={opt == @selected}>{opt}</option>
      </select>
    </form>
    """
  end
end
```

`phx-target={@myself}` is what routes the event to the component instead of the parent
LiveView. Components talk to their parent with `send(self(), …)` and a `handle_info/2`.

## Fan-out from contexts

Broadcast from the context after the write commits, never from the LiveView. Every
subscriber then gets the same event, including the one that caused it.

```elixir
def create_order(attrs) do
  with {:ok, order} <- %Order{} |> Order.changeset(attrs) |> Repo.insert() do
    Phoenix.PubSub.broadcast(MyApp.PubSub, "orders", {:order_created, order})
    {:ok, order}
  end
end
```

## Channels and Presence

Channels are for non-LiveView clients (mobile, JS SDKs, anything holding its own state).
Presence tracks who is on a topic and diffs joins and leaves in real time.

Presence needs a module of your own plus a supervision-tree entry between the PubSub
server and the endpoint:

```elixir
defmodule MyAppWeb.Presence do
  use Phoenix.Presence, otp_app: :my_app, pubsub_server: MyApp.PubSub
end

# lib/my_app/application.ex
children = [
  MyApp.Repo,
  {Phoenix.PubSub, name: MyApp.PubSub},
  MyAppWeb.Presence,
  MyAppWeb.Endpoint
]
```

```elixir
defmodule MyAppWeb.RoomChannel do
  use MyAppWeb, :channel
  alias MyAppWeb.Presence

  @impl true
  def join("room:" <> room_id, _payload, socket) do
    if authorized?(socket, room_id) do
      send(self(), :after_join)
      {:ok, assign(socket, :room_id, room_id)}
    else
      {:error, %{reason: "unauthorized"}}
    end
  end

  @impl true
  def handle_info(:after_join, socket) do
    {:ok, _ref} =
      Presence.track(socket, socket.assigns.user_id, %{
        online_at: System.system_time(:second)
      })

    push(socket, "presence_state", Presence.list(socket))
    {:noreply, socket}
  end
end
```

`join/3` is the authorization boundary: check the topic against the socket's identity
there, because everything after it is already inside the room. Keep presence metadata
small and extend it in the `fetch/2` callback rather than per-subscriber queries.

## Testing

`Phoenix.LiveViewTest` drives the real LiveView process over a test socket, so it exercises
mount, events and diffs together. Prefer it over asserting on rendered strings from a
controller.

```elixir
defmodule MyAppWeb.OrdersLiveTest do
  use MyAppWeb.ConnCase, async: true
  import Phoenix.LiveViewTest

  test "archiving removes the row", %{conn: conn} do
    order = order_fixture()
    {:ok, view, html} = live(conn, ~p"/orders")
    assert html =~ order.reference

    view |> element("button[phx-value-id='#{order.id}']") |> render_click()
    refute render(view) =~ order.reference
  end

  test "a broadcast reaches a mounted view", %{conn: conn} do
    {:ok, view, _html} = live(conn, ~p"/orders")
    {:ok, order} = Orders.create_order(valid_attrs())
    assert render(view) =~ order.reference
  end
end
```

`element/3` selects by CSS and fails loudly when the selector matches nothing or several
nodes, which makes it a better assertion than a substring match. `async: true` works
because `DataCase`/`ConnCase` wrap each test in a sandboxed transaction.

## Ops

- **Telemetry**: Phoenix emits `[:phoenix, :endpoint, :stop]`, `[:phoenix, :live_view, …]`
  and Ecto query events. Export with `:telemetry_poller`, `OpentelemetryPhoenix` and
  `OpentelemetryEcto`; watch LiveView diff sizes as a first-class metric.
- **Releases**: `MIX_ENV=prod mix release`, runtime configuration in `config/runtime.exs`
  (read env vars there, not in `config/prod.exs`), start with
  `PHX_SERVER=true _build/prod/rel/my_app/bin/my_app start`.
- **Assets**: `mix assets.deploy` builds and digests; it must run before the release.
- **Clustering**: `libcluster` with a DNS or epmd strategy. PubSub and Presence go
  distributed automatically once the nodes see each other.
- **Background work**: Oban, supervised in the application tree, for anything with
  retries or a schedule. Long CPU work never runs in a LiveView process.
- **Caching**: ETS or Cachex on hot paths, supervised, short TTLs, invalidated on write.

## Pitfalls

- Subscribing outside the `connected?/1` guard, so the dead render subscribes too.
- Holding a growing collection in assigns instead of a stream.
- Querying in `render/1`. Render is pure: assign in `mount`/`handle_event`, render from
  assigns.
- A stream container without `phx-update="stream"`, or children without the stream
  `dom_id` — updates silently do nothing.
- Blocking the LiveView process on a slow call. Wrap it in `start_async/3` or push the
  work to Oban and let the broadcast update the view.
- Unsupervised ETS tables that nothing ever trims.

## Reference commands

- `mix phx.routes` — every route and LiveView path.
- `mix phx.gen.live Accounts User users email:string` — CRUD scaffold; review the context
  boundary it invents before keeping it.
- `mix test --seed 0 --max-failures 1` — deterministic ordering, stop at the first failure.
- `mix format && mix credo --strict && mix dialyzer`.
- `mix compile --warnings-as-errors` — the check CI should gate on.
