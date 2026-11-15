import { useCallback, useEffect, useState } from "react";
import { Booking, Slot, getSlots } from "./api";
import SlotPicker from "./components/SlotPicker";
import BookingForm from "./components/BookingForm";
import Confirmation from "./components/Confirmation";
import MyBookings from "./components/MyBookings";

export default function App() {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [providers, setProviders] = useState<string[]>([]);
  const [provider, setProvider] = useState("");
  const [selected, setSelected] = useState<Slot | null>(null);
  const [confirmed, setConfirmed] = useState<{ booking: Booking; slot?: Slot } | null>(null);
  const [status, setStatus] = useState("Loading slots…");
  const [refreshKey, setRefreshKey] = useState(0);

  const load = useCallback(async () => {
    try {
      const { slots: list } = await getSlots(provider);
      setSlots(list);
      if (!provider) setProviders([...new Set(list.map((s) => s.provider))]);
      const free = list.filter((s) => s.available).length;
      setStatus(list.length ? `${free} of ${list.length} slots available` : "No slots yet.");
    } catch (e) {
      setStatus("Could not load slots: " + (e instanceof Error ? e.message : "unknown error"));
    }
  }, [provider]);

  useEffect(() => {
    void load();
  }, [load]);

  function handleBooked(booking: Booking) {
    setConfirmed({ booking, slot: slots.find((s) => s.id === booking.slot_id) });
    setSelected(null);
    setRefreshKey((k) => k + 1);
    void load();
  }

  return (
    <>
      <header>
        <h1>Book a clinic appointment</h1>
        <p>Pick an available slot, enter your details and confirm.</p>
      </header>
      <main>
        <SlotPicker
          slots={slots}
          providers={providers}
          provider={provider}
          onProviderChange={setProvider}
          selectedId={selected?.id ?? null}
          onSelect={(s) => {
            setSelected(s);
            setConfirmed(null);
          }}
          status={status}
        />
        {selected && (
          <BookingForm
            key={selected.id}
            slot={selected}
            onBooked={handleBooked}
            onSlotTaken={() => {
              setSelected(null);
              void load();
            }}
          />
        )}
        {confirmed && <Confirmation booking={confirmed.booking} slot={confirmed.slot} />}
        <MyBookings
          slots={slots}
          refreshKey={refreshKey}
          onCancelled={() => {
            void load();
          }}
        />
      </main>
    </>
  );
}
