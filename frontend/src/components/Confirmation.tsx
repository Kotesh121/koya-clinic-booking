import { Booking, Slot, fmtTime } from "../api";

export default function Confirmation({ booking, slot }: { booking: Booking; slot?: Slot }) {
  const rows: [string, string][] = [
    ["Booking ID", booking.id],
    ["Name", booking.name],
    ["Email", booking.email],
    ["Provider", slot ? slot.provider : booking.slot_id],
    ["Time", slot ? fmtTime(slot.start) : "—"],
    ["Status", booking.status],
  ];
  return (
    <section>
      <h2>Booking confirmed ✅</h2>
      <dl>
        {rows.map(([k, v]) => (
          <div key={k} style={{ display: "contents" }}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
