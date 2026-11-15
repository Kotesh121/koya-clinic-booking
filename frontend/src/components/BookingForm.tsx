import { FormEvent, useRef, useState } from "react";
import { ApiError, Booking, Slot, createBooking, fmtTime } from "../api";

interface Props {
  slot: Slot;
  onBooked: (b: Booking) => void;
  onSlotTaken: () => void;
}

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export default function BookingForm({ slot, onBooked, onSlotTaken }: Props) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  // Reuse the same Idempotency-Key if the same booking is retried, so it can never be booked twice.
  const keyRef = useRef<{ sig: string; key: string } | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    const n = name.trim();
    const em = email.trim();
    if (!n) return setError("Please enter your name.");
    if (!EMAIL_RE.test(em)) return setError("Please enter a valid email.");

    const sig = `${slot.id}|${n}|${em}`;
    if (!keyRef.current || keyRef.current.sig !== sig) keyRef.current = { sig, key: crypto.randomUUID() };

    setBusy(true);
    try {
      const booking = await createBooking({ slot_id: slot.id, name: n, email: em }, keyRef.current.key);
      keyRef.current = null;
      onBooked(booking);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        keyRef.current = null;
        setError("Sorry, that slot was just taken. Please pick another.");
        onSlotTaken();
      } else if (err instanceof ApiError && err.status === 429) {
        setError(`Too many attempts. Try again in ${err.retryAfter ?? "a few"} seconds.`);
      } else {
        setError(err instanceof Error ? err.message : "Something went wrong.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <h2>Your details</h2>
      <p className="muted">
        {slot.provider} — {fmtTime(slot.start)}
      </p>
      <form onSubmit={submit} noValidate>
        <label>
          Full name
          <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
        </label>
        <label>
          Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        </label>
        <button type="submit" disabled={busy}>
          {busy ? "Booking…" : "Confirm booking"}
        </button>
      </form>
      <p className="error" role="alert">
        {error}
      </p>
    </section>
  );
}
