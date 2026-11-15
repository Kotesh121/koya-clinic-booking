import { FormEvent, useState } from "react";
import { Booking, Slot, cancelBooking, fmtTime, getAllBookings } from "../api";

interface Props {
  slots: Slot[];
  refreshKey: number;
  onCancelled: () => void;
}

export default function MyBookings({ slots, refreshKey, onCancelled }: Props) {
  const [email, setEmail] = useState("");
  const [looked, setLooked] = useState("");
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [status, setStatus] = useState("");
  const [lastRefresh, setLastRefresh] = useState(refreshKey);

  async function load(addr: string) {
    setStatus("Loading…");
    try {
      const list = await getAllBookings(addr);
      setBookings(list);
      setLooked(addr);
      setStatus(list.length ? "" : "No bookings found for that email.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Could not load bookings.");
    }
  }

  // A new booking was just made: refresh the list if one is on screen.
  if (refreshKey !== lastRefresh) {
    setLastRefresh(refreshKey);
    if (looked) void load(looked);
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (email.trim()) await load(email.trim());
  }

  async function cancel(id: string) {
    try {
      await cancelBooking(id);
      await load(looked);
      onCancelled();
    } catch (e) {
      setStatus(e instanceof Error ? e.message : "Could not cancel.");
    }
  }

  return (
    <section>
      <h2>My bookings</h2>
      <form className="inline" onSubmit={submit} noValidate>
        <input type="email" placeholder="Your email" value={email} onChange={(e) => setEmail(e.target.value)} />
        <button type="submit">Look up</button>
      </form>
      <p className="muted">{status}</p>
      <ul>
        {bookings.map((b) => {
          const slot = slots.find((s) => s.id === b.slot_id);
          return (
            <li key={b.id}>
              <span>
                {slot ? `${slot.provider} — ${fmtTime(slot.start)} ` : `Slot ${b.slot_id} `}
                <span className={"tag" + (b.status === "cancelled" ? " cancelled" : "")}>{b.status}</span>
              </span>
              {b.status === "confirmed" && (
                <button className="danger" onClick={() => cancel(b.id)}>
                  Cancel
                </button>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
