import { Slot, fmtTime } from "../api";

interface Props {
  slots: Slot[];
  providers: string[];
  provider: string;
  onProviderChange: (p: string) => void;
  selectedId: string | null;
  onSelect: (s: Slot) => void;
  status: string;
}

export default function SlotPicker({ slots, providers, provider, onProviderChange, selectedId, onSelect, status }: Props) {
  const byProvider = slots.reduce<Record<string, Slot[]>>((acc, s) => {
    (acc[s.provider] ||= []).push(s);
    return acc;
  }, {});

  return (
    <section>
      <div className="row">
        <h2>Available slots</h2>
        <select value={provider} onChange={(e) => onProviderChange(e.target.value)} aria-label="Filter by provider">
          <option value="">All providers</option>
          {providers.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </div>
      <p className="muted">{status}</p>
      {Object.entries(byProvider).map(([name, list]) => (
        <div key={name}>
          <div className="provider">{name}</div>
          <div className="slot-grid">
            {list.map((s) => (
              <button
                key={s.id}
                type="button"
                className={"slot" + (selectedId === s.id ? " selected" : "")}
                disabled={!s.available}
                title={s.available ? "Select this slot" : "Already booked"}
                onClick={() => onSelect(s)}
              >
                {fmtTime(s.start)}
              </button>
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}
