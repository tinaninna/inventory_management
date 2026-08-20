import { useMemo, useState } from "react";
import { api } from "./api";
import type { BuildHistoryItem, BuildLine, BomItem, InventoryItem, LegacyDashboard, LegacyProject } from "./types";

interface Props { projects: LegacyProject[]; dashboard: LegacyDashboard | null; }
const display = (value: string | null) => value || "Not provided";

export function ProjectsPage({ projects, dashboard }: Props) {
  const [selected, setSelected] = useState<number | null>(null);
  const [bom, setBom] = useState<BomItem[]>([]);
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [builds, setBuilds] = useState<BuildHistoryItem[]>([]);
  const [quantity, setQuantity] = useState("1");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const project = projects.find((item) => item.id === selected);
  const parsedQuantity = Number(quantity);
  const validQuantity = Number.isInteger(parsedQuantity) && parsedQuantity > 0;
  const stockByComponent = useMemo(() => new Map(inventory.map((item) => [item.component_id, item])), [inventory]);
  const preview = useMemo<BuildLine[]>(() => bom.map((item) => {
    const required = item.quantity_required * (validQuantity ? parsedQuantity : 0);
    const available = stockByComponent.get(item.component_id)?.available_quantity ?? 0;
    const shortage = Math.max(required - available, 0);
    return { component_id: item.component_id, manufacturer_part_number: item.manufacturer_part_number, required_quantity: required, previous_available_quantity: available, consumed_quantity: shortage ? 0 : required, remaining_available_quantity: shortage ? available : available - required, shortage_quantity: shortage };
  }), [bom, parsedQuantity, stockByComponent, validQuantity]);
  const shortages = preview.filter((line) => line.shortage_quantity > 0);

  const openProject = async (id: number) => {
    setSelected(id); setError(""); setMessage(""); setLoading(true);
    try {
      const [projectBom, stock, history] = await Promise.all([api.getProjectBom(id), api.getInventory(), api.getProjectBuilds(id)]);
      setBom(projectBom); setInventory(stock); setBuilds(history);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not load project build data."); }
    finally { setLoading(false); }
  };

  const refreshBuildData = async () => {
    if (selected === null) return;
    const [stock, history] = await Promise.all([api.getInventory(), api.getProjectBuilds(selected)]);
    setInventory(stock); setBuilds(history);
  };

  const submitBuild = async () => {
    if (selected === null || !validQuantity || shortages.length > 0 || submitting) return;
    setSubmitting(true); setError(""); setMessage("");
    try {
      const result = await api.buildProject(selected, parsedQuantity);
      if (!result.success) { setError("The build was not completed because inventory is insufficient."); return; }
      setMessage(`Build #${result.build_id} completed. Inventory has been refreshed.`);
      await refreshBuildData();
    } catch (caught) { setError(caught instanceof Error ? caught.message : "The build could not be completed."); }
    finally { setSubmitting(false); }
  };

  return <div className="space-y-7">
    <section className="panel"><PanelHeading title="Project BOMs" detail="Select a project to preview and confirm a build." />
      {!projects.length ? <EmptyState title="No projects found" detail="Projects appear after BOM data is loaded." /> : <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{projects.map((item) => { const summary = dashboard?.projects.find((entry) => entry.id === item.id); return <button className={`project-tile ${selected === item.id ? "project-tile-active" : ""}`} key={item.id} onClick={() => void openProject(item.id)}><div className="flex items-start justify-between gap-4"><h3 className="font-semibold">{item.name}</h3><span aria-hidden="true">→</span></div><p className="mt-5 text-sm text-[#7c8b84]">{summary?.component_count ?? "—"} components · {summary?.total_quantity_required ?? "—"} required units</p></button>; })}</div>}
    </section>
    {selected !== null && <>
      <section className="panel"><div className="flex flex-col gap-4 border-b border-[#edf1ee] pb-5 sm:flex-row sm:items-end sm:justify-between"><div><h2 className="section-title">Build {project?.name ?? "project"}</h2><p className="mt-1 text-sm text-[#7c8b84]">Review every component before confirming inventory consumption.</p></div><div><label className="mb-1 block text-xs font-bold uppercase tracking-[.08em] text-[#7c8b84]" htmlFor="build-quantity">Build quantity</label><input id="build-quantity" className="input w-36" type="number" min="1" step="1" value={quantity} onChange={(event) => { setQuantity(event.target.value); setError(""); setMessage(""); }} /></div></div>
        {!validQuantity && <p className="mt-4 text-sm font-semibold text-[#b42318]" role="alert">Enter a whole number greater than zero.</p>}
        {error && <div className="alert-error mt-4" role="alert">{error}</div>}
        {message && <div className="mt-4 rounded-xl border border-[#c3e0d3] bg-[#e8f2ee] px-4 py-3 text-sm font-semibold text-[#236451]" role="status">{message}</div>}
        {loading ? <LoadingState /> : <><div className="table-wrap mt-5"><table className="data-table"><thead><tr><th>Part number</th><th>Description</th><th>Required</th><th>Available</th><th>Remaining</th><th>Status</th></tr></thead><tbody>{preview.map((line) => { const item = bom.find((entry) => entry.component_id === line.component_id); return <tr key={line.component_id}><td className="font-mono font-semibold text-[#1a4d3f]">{line.manufacturer_part_number}</td><td>{display(item?.description ?? null)}</td><td className="tabular-nums">{line.required_quantity}</td><td className="tabular-nums">{line.previous_available_quantity}</td><td className="tabular-nums">{line.remaining_available_quantity}</td><td><span className={`status-pill ${line.shortage_quantity ? "status-red" : "status-green"}`}>{line.shortage_quantity ? `Short by ${line.shortage_quantity}` : "Sufficient"}</span></td></tr>; })}</tbody></table></div>{shortages.length > 0 && <div className="mt-5 rounded-xl border border-[#f3cec8] bg-[#fdecea] p-4 text-sm text-[#963029]" role="alert"><p className="font-bold">Build cannot be confirmed</p><ul className="mt-2 space-y-1">{shortages.map((line) => <li key={line.component_id}>{line.manufacturer_part_number}: requires {line.required_quantity}, has {line.previous_available_quantity}, shortage {line.shortage_quantity}.</li>)}</ul></div>}<button className="button-primary mt-5" disabled={!validQuantity || shortages.length > 0 || submitting} onClick={() => void submitBuild()}>{submitting ? <><span className="spinner spinner-light" /> Confirming build...</> : <>Build Project <span aria-hidden="true">→</span></>}</button></>}
      </section>
      <section className="panel"><PanelHeading title="Build history" detail="Completed builds recorded for this project." />{builds.length ? <div className="divide-y divide-[#edf1ed]">{builds.map((build) => <div className="flex items-center justify-between gap-4 py-3" key={build.id}><div><p className="font-semibold">Build #{build.id}</p><p className="text-xs text-[#7c8b84]">{new Date(build.created_at).toLocaleString()}</p></div><div className="text-right"><span className="status-pill status-green">{build.status}</span><p className="mt-1 text-xs text-[#7c8b84]">Quantity {build.build_quantity}</p></div></div>)}</div> : <EmptyState title="No builds recorded" detail="A confirmed build will appear here." />}</section>
    </>}
  </div>;
}

function PanelHeading({ title, detail }: { title: string; detail: string }) { return <div className="mb-2 border-b border-[#edf1ee] pb-4"><h2 className="section-title">{title}</h2><p className="mt-1 text-sm text-[#7c8b84]">{detail}</p></div>; }
function EmptyState({ title, detail }: { title: string; detail: string }) { return <div className="py-12 text-center"><p className="font-semibold text-[#374842]">{title}</p><p className="mt-1 text-sm text-[#8b9992]">{detail}</p></div>; }
function LoadingState() { return <div className="flex min-h-40 items-center justify-center text-sm text-[#5c6d66]"><span className="spinner" aria-hidden="true" /> Loading build data...</div>; }
