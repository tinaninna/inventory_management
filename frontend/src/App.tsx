import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "./api";
import { BarChart, DonutChart } from "./charts";
import { ProjectsPage } from "./ProjectBuildPage";
import logoMark from "./assets/spwes-mark.png";
import type { BomItem, ImportJob, ImportSummary, InventoryItem, LegacyDashboard, LegacyProject, View } from "./types";

const navItems: { id: View; label: string; icon: string }[] = [
  { id: "dashboard", label: "Dashboard", icon: "◒" },
  { id: "inventory", label: "Inventory", icon: "▤" },
  { id: "projects", label: "Projects", icon: "⌘" },
  { id: "import", label: "Import Excel", icon: "↑" },
  { id: "reports", label: "Reports", icon: "▥" },
];
const formatDate = (value: string | null) => (value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "—");
const display = (value: string | null) => value || "Not provided";

export function App() {
  const [view, setView] = useState<View>(() => (location.hash.slice(1) as View) || "dashboard");
  const [inventory, setInventory] = useState<InventoryItem[]>([]);
  const [lowStock, setLowStock] = useState<InventoryItem[]>([]);
  const [imports, setImports] = useState<ImportJob[]>([]);
  const [legacyDashboard, setLegacyDashboard] = useState<LegacyDashboard | null>(null);
  const [projects, setProjects] = useState<LegacyProject[]>([]);
  const [totalBuilds, setTotalBuilds] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [lastImport, setLastImport] = useState<ImportSummary | null>(null);

  const refreshInventory = async () => {
    const [items, low, history] = await Promise.all([api.getInventory(), api.getLowStock(), api.getImports()]);
    setInventory(items);
    setLowStock(low);
    setImports(history);
  };

  useEffect(() => {
    const onHash = () => {
      const next = location.hash.slice(1) as View;
      setView(navItems.some((item) => item.id === next) ? next : "dashboard");
    };
    window.addEventListener("hashchange", onHash);
    void (async () => {
      try {
        await refreshInventory();
        const [dashboard, projectList] = await Promise.all([api.getLegacyDashboard(), api.getProjects()]);
        setLegacyDashboard(dashboard);
        setProjects(projectList);
        try {
          const builds = await Promise.all(projectList.map((project) => api.getProjectBuilds(project.id)));
          setTotalBuilds(builds.reduce((sum, list) => sum + list.length, 0));
        } catch {
          setTotalBuilds(null);
        }
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not connect to the API.");
      } finally {
        setLoading(false);
      }
    })();
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const navigate = (next: View) => {
    location.hash = next;
    setView(next);
  };
  const onImported = async (summary: ImportSummary) => {
    setLastImport(summary);
    await refreshInventory();
    navigate("import");
  };

  return (
    <div className="min-h-screen w-full max-w-full bg-[#f5f7f5] text-[#1c2d27]">
      <aside className="sidebar">
        <Brand />
        <nav className="mt-10 space-y-1.5" aria-label="Primary navigation">
          {navItems.map((item) => (
            <button key={item.id} onClick={() => navigate(item.id)} className={`nav-item ${view === item.id ? "nav-item-active" : ""}`} aria-current={view === item.id ? "page" : undefined}>
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="mt-auto rounded-xl border border-[#1c5142] bg-[#1a4d3f] p-4 text-sm leading-6 text-[#c7dbd3]">
          <p className="font-semibold text-white">Inventory Control</p>
          <p className="mt-1">Track stock levels, manage projects, and import data with confidence.</p>
        </div>
      </aside>
      <div className="w-full max-w-full lg:pl-64">
        <header className="w-full border-b border-[#e2e9e5] bg-[#f9fbfa]/95 px-5 py-4 backdrop-blur lg:hidden">
          <div className="flex items-center justify-between gap-3">
            <Brand compact />
            <button className="button-primary shrink-0" onClick={() => navigate("import")}>
              <span aria-hidden="true">↑</span> Import Excel
            </button>
          </div>
          <nav className="mt-4 flex gap-1 overflow-x-auto" aria-label="Mobile navigation">
            {navItems.map((item) => (
              <button key={item.id} onClick={() => navigate(item.id)} className={`mobile-nav-item ${view === item.id ? "mobile-nav-active" : ""}`}>
                {item.label}
              </button>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-[1440px] px-5 py-8 sm:px-8 lg:px-10 lg:py-10">
          <PageHeader view={view} onImport={() => navigate("import")} />
          {error && (
            <div className="alert-error mb-6" role="alert">
              <strong>Connection issue.</strong> {error}
            </div>
          )}
          {loading ? (
            <LoadingState />
          ) : (
            <>
              {view === "dashboard" && (
                <Dashboard inventory={inventory} lowStock={lowStock} imports={imports} legacy={legacyDashboard} totalBuilds={totalBuilds} onNavigate={navigate} />
              )}
              {view === "inventory" && <InventoryPage inventory={inventory} />}
              {view === "import" && <ImportPage lastImport={lastImport} onImported={onImported} />}
              {view === "projects" && <ProjectsPage projects={projects} dashboard={legacyDashboard} />}
              {view === "reports" && <ReportsPage inventory={inventory} imports={imports} legacy={legacyDashboard} />}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      <img src={logoMark} alt="SPWES logo" className="brand-mark" />
      <div className="min-w-0">
        <strong className={`block truncate text-sm font-extrabold tracking-tight ${compact ? "text-[#143c31]" : "text-[#7fdcb8]"}`}>SPWES</strong>
        {!compact && <span className="block text-[10px] leading-tight text-[#a9c4ba]">Sustainable Power and Water Engineering Solution</span>}
      </div>
    </div>
  );
}

function PageHeader({ view, onImport }: { view: View; onImport: () => void }) {
  const content: Record<View, [string, string]> = {
    dashboard: ["Dashboard", "Overview of inventory, projects, stock levels, and recent imports."],
    inventory: ["Inventory", "Search current stock levels, reservations, and reorder needs."],
    import: ["Import Excel", "Upload the latest Excel stock report to reconcile quantities safely."],
    projects: ["Projects", "Review existing BOM requirements and confirm builds."],
    reports: ["Reports", "Stock distribution, project usage, and import activity at a glance."],
  };
  return (
    <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div className="min-w-0">
        <p className="eyebrow">Inventory management</p>
        <h1 className="page-title mt-1">{content[view][0]}</h1>
        <p className="mt-2 max-w-2xl text-[15px] leading-6 text-[#5c6d66]">{content[view][1]}</p>
      </div>
      {view !== "import" && (
        <button className="button-primary shrink-0 self-start sm:self-auto" onClick={onImport}>
          <span aria-hidden="true">↑</span> Import Excel
        </button>
      )}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="panel flex min-h-56 items-center justify-center text-sm text-[#5c6d66]">
      <span className="spinner" aria-hidden="true" /> Loading inventory data...
    </div>
  );
}
function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="py-12 text-center">
      <p className="font-semibold text-[#374842]">{title}</p>
      <p className="mt-1 text-sm text-[#8b9992]">{detail}</p>
    </div>
  );
}
function Metric({ label, value, note, tone = "brand" }: { label: string; value: number | string; note: string; tone?: string }) {
  const icon = tone === "amber" ? "!" : tone === "red" ? "×" : tone === "blue" ? "◆" : "✓";
  return (
    <article className="metric">
      <div className={`metric-icon metric-${tone}`} aria-hidden="true">{icon}</div>
      <div className="min-w-0">
        <p className="truncate text-sm font-semibold text-[#5c6d66]">{label}</p>
        <p className="mt-1 text-2xl font-bold tracking-tight text-[#152621]">{value}</p>
        <p className="mt-1 truncate text-xs text-[#8b9992]">{note}</p>
      </div>
    </article>
  );
}
function PanelHeading({ title, detail, action, onAction }: { title: string; detail: string; action?: string; onAction?: () => void }) {
  return (
    <div className="mb-4 flex flex-col gap-3 border-b border-[#edf1ee] pb-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h2 className="section-title">{title}</h2>
        <p className="mt-1 text-sm text-[#7c8b84]">{detail}</p>
      </div>
      {action && onAction && (
        <button className="text-button shrink-0" onClick={onAction}>
          {action} <span aria-hidden="true">→</span>
        </button>
      )}
    </div>
  );
}

function stockBreakdown(inventory: InventoryItem[]) {
  const outOfStock = inventory.filter((item) => item.available_quantity <= 0).length;
  const lowStockOnly = inventory.filter((item) => item.available_quantity > 0 && item.requires_reorder).length;
  const inStock = inventory.length - outOfStock - lowStockOnly;
  return { inStock, lowStockOnly, outOfStock, total: inventory.length };
}
function topComponents(inventory: InventoryItem[], count = 10) {
  return [...inventory]
    .sort((a, b) => b.quantity_on_hand - a.quantity_on_hand)
    .slice(0, count)
    .map((item) => ({ label: item.manufacturer_part_number, value: item.quantity_on_hand }));
}

function Dashboard({ inventory, lowStock, imports, legacy, totalBuilds, onNavigate }: { inventory: InventoryItem[]; lowStock: InventoryItem[]; imports: ImportJob[]; legacy: LegacyDashboard | null; totalBuilds: number | null; onNavigate: (view: View) => void }) {
  const breakdown = useMemo(() => stockBreakdown(inventory), [inventory]);
  const bars = useMemo(() => topComponents(inventory), [inventory]);
  const donutSlices = [
    { label: "In Stock", value: breakdown.inStock, color: "#236451" },
    { label: "Low Stock", value: breakdown.lowStockOnly, color: "#b45309" },
    { label: "Out of Stock", value: breakdown.outOfStock, color: "#b42318" },
  ];

  return (
    <div className="w-full max-w-full space-y-7">
      <div className="grid w-full max-w-full grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Metric label="Total Components" value={inventory.length} note="All components" tone="brand" />
        <Metric label="In Stock" value={breakdown.inStock} note="Components with stock" tone="brand" />
        <Metric label="Low Stock Items" value={breakdown.lowStockOnly} note="Below reorder point" tone="amber" />
        <Metric label="Total Projects" value={legacy?.project_count ?? 0} note="Active projects" tone="blue" />
        <Metric label="Total Builds" value={totalBuilds ?? "—"} note="Completed builds" tone="blue" />
      </div>

      <div className="grid w-full max-w-full grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="panel w-full min-w-0">
          <PanelHeading title="Stock Status Overview" detail="Share of components by current availability." />
          <DonutChart slices={donutSlices} total={breakdown.total} centerLabel="Total" />
        </section>
        <section className="panel w-full min-w-0">
          <PanelHeading title="Top 10 Components by Stock Quantity" detail="Highest on-hand quantities across your catalog." />
          <BarChart data={bars} color="#236451" />
        </section>
      </div>

      <section className="panel w-full min-w-0">
        <PanelHeading title="Stock Attention" detail="Items at or below their reorder point." action="View all" onAction={() => onNavigate("inventory")} />
        {lowStock.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Part Number</th>
                  <th>Description</th>
                  <th className="text-right">Available Qty</th>
                  <th className="text-right">Reorder Point</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {lowStock.slice(0, 8).map((item) => (
                  <tr key={item.id}>
                    <td className="font-mono font-semibold text-[#1a4d3f]">{item.manufacturer_part_number}</td>
                    <td>{display(item.description)}</td>
                    <td className="text-right tabular-nums font-semibold">{item.available_quantity}</td>
                    <td className="text-right tabular-nums">{item.reorder_point}</td>
                    <td><StockStatus item={item} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="Inventory is in good shape" detail="No components are currently at or below their reorder point." />
        )}
      </section>

      <section className="panel w-full min-w-0">
        <PanelHeading title="Import History" detail="A record of inventory reconciliation runs." action="View all" onAction={() => onNavigate("import")} />
        {imports.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>File Name</th>
                  <th>Imported At</th>
                  <th>Imported By</th>
                  <th>Status</th>
                  <th className="text-right">Records</th>
                </tr>
              </thead>
              <tbody>
                {imports.slice(0, 6).map((job) => (
                  <tr key={job.id}>
                    <td className="tabular-nums text-[#7c8b84]">{job.id}</td>
                    <td className="max-w-[220px] truncate font-semibold">{job.filename}</td>
                    <td className="whitespace-nowrap text-[#5c6d66]">{formatDate(job.completed_at ?? job.started_at)}</td>
                    <td className="text-[#8b9992]">—</td>
                    <td><span className={`status-pill ${job.status === "completed" ? "status-green" : "status-red"}`}>{job.status}</span></td>
                    <td className="text-right tabular-nums">{job.rows_processed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No imports yet" detail="Upload an Excel inventory report to begin." />
        )}
      </section>

      {legacy && (
        <section className="panel w-full min-w-0">
          <PanelHeading title="BOM Workspace" detail="Existing project requirements remain available while inventory is managed separately." action="Open projects" onAction={() => onNavigate("projects")} />
          <div className="grid w-full max-w-full grid-cols-1 gap-4 sm:grid-cols-3">
            <MiniStat label="BOM components" value={legacy.component_count} />
            <MiniStat label="Projects" value={legacy.project_count} />
            <MiniStat label="BOM items" value={legacy.bom_item_count} />
          </div>
        </section>
      )}
    </div>
  );
}
function MiniStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-0 rounded-xl border border-[#e2e9e5] bg-[#f7faf8] p-4">
      <p className="truncate text-xs uppercase tracking-[.1em] text-[#7c8b84]">{label}</p>
      <p className="mt-2 text-xl font-bold">{value}</p>
    </div>
  );
}
function StockStatus({ item }: { item: InventoryItem }) {
  const label = item.available_quantity <= 0 ? "Out of Stock" : item.requires_reorder ? "Low Stock" : "In Stock";
  const tone = item.available_quantity <= 0 ? "status-red" : item.requires_reorder ? "status-amber" : "status-green";
  return (
    <span className={`status-pill ${tone}`}>
      <span className="status-dot" aria-hidden="true" /> {label}
    </span>
  );
}

function ReportsPage({ inventory, imports, legacy }: { inventory: InventoryItem[]; imports: ImportJob[]; legacy: LegacyDashboard | null }) {
  const breakdown = useMemo(() => stockBreakdown(inventory), [inventory]);
  const bars = useMemo(() => topComponents(inventory, 10), [inventory]);
  const donutSlices = [
    { label: "In Stock", value: breakdown.inStock, color: "#236451" },
    { label: "Low Stock", value: breakdown.lowStockOnly, color: "#b45309" },
    { label: "Out of Stock", value: breakdown.outOfStock, color: "#b42318" },
  ];
  const projectBars = (legacy?.projects ?? []).map((project) => ({ label: project.name, value: project.component_count }));

  return (
    <div className="w-full max-w-full space-y-7">
      <div className="grid w-full max-w-full grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Metric label="Low Stock Count" value={breakdown.lowStockOnly} note="Below reorder point" tone="amber" />
        <Metric label="Out of Stock Count" value={breakdown.outOfStock} note="No available quantity" tone="red" />
        <Metric label="Total Imports" value={imports.length} note="Reconciliation runs recorded" tone="blue" />
        <Metric label="BOM Items" value={legacy?.bom_item_count ?? 0} note="Across all projects" tone="brand" />
      </div>

      <div className="grid w-full max-w-full grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="panel w-full min-w-0">
          <PanelHeading title="Stock Distribution" detail="Current inventory health across your catalog." />
          <DonutChart slices={donutSlices} total={breakdown.total} centerLabel="Total" />
        </section>
        <section className="panel w-full min-w-0">
          <PanelHeading title="Top 10 Components by Stock Quantity" detail="Highest on-hand quantities across your catalog." />
          <BarChart data={bars} color="#236451" />
        </section>
      </div>

      <section className="panel w-full min-w-0">
        <PanelHeading title="Components by Project" detail="Distinct BOM components required per project." />
        {projectBars.length ? <BarChart data={projectBars} color="#135dad" /> : <EmptyState title="No project data" detail="Projects appear once BOM data is loaded." />}
      </section>

      <section className="panel w-full min-w-0">
        <PanelHeading title="Recent Import Activity" detail="The most recent inventory reconciliation runs." />
        {imports.length ? (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Imported At</th>
                  <th>Status</th>
                  <th className="text-right">Rows Processed</th>
                  <th className="text-right">Updated</th>
                  <th className="text-right">Needs Attention</th>
                </tr>
              </thead>
              <tbody>
                {imports.slice(0, 10).map((job) => (
                  <tr key={job.id}>
                    <td className="max-w-[220px] truncate font-semibold">{job.filename}</td>
                    <td className="whitespace-nowrap text-[#5c6d66]">{formatDate(job.completed_at ?? job.started_at)}</td>
                    <td><span className={`status-pill ${job.status === "completed" ? "status-green" : "status-red"}`}>{job.status}</span></td>
                    <td className="text-right tabular-nums">{job.rows_processed}</td>
                    <td className="text-right tabular-nums">{job.updated_components}</td>
                    <td className="text-right tabular-nums">{job.invalid_rows + job.unmatched_rows}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No imports yet" detail="Upload an Excel inventory report to begin." />
        )}
      </section>
    </div>
  );
}

function InventoryPage({ inventory }: { inventory: InventoryItem[] }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const filtered = useMemo(
    () =>
      inventory.filter((item) => {
        const matches = [item.manufacturer_part_number, item.description, item.manufacturer, item.value].join(" ").toLowerCase().includes(query.toLowerCase());
        const status = filter === "low" ? item.requires_reorder : filter === "available" ? item.available_quantity > item.reorder_point : true;
        return matches && status;
      }),
    [inventory, query, filter]
  );
  return (
    <section className="panel w-full min-w-0">
      <div className="flex flex-col gap-4 border-b border-[#edf1ee] pb-5 lg:flex-row lg:items-center lg:justify-between">
        <div className="min-w-0">
          <h2 className="section-title">Current Stock</h2>
          <p className="mt-1 text-sm text-[#7c8b84]">{filtered.length} of {inventory.length} inventory items</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <label className="sr-only" htmlFor="inventory-search">Search inventory</label>
          <input id="inventory-search" className="input sm:w-64" placeholder="Search part number or description" value={query} onChange={(event) => setQuery(event.target.value)} />
          <label className="sr-only" htmlFor="stock-filter">Filter stock</label>
          <select id="stock-filter" className="input sm:w-44" value={filter} onChange={(event) => setFilter(event.target.value)}>
            <option value="all">All stock</option>
            <option value="low">Low stock</option>
            <option value="available">Healthy stock</option>
          </select>
        </div>
      </div>
      <div className="table-wrap mt-5">
        <table className="data-table">
          <thead>
            <tr>
              <th>Part number</th>
              <th>Description</th>
              <th>Manufacturer</th>
              <th className="text-right">On hand</th>
              <th className="text-right">Reserved</th>
              <th className="text-right">Available</th>
              <th className="text-right">Reorder point</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((item) => (
              <tr key={item.id}>
                <td className="font-mono font-semibold text-[#1a4d3f]">{item.manufacturer_part_number}</td>
                <td>{display(item.description)}</td>
                <td>{display(item.manufacturer)}</td>
                <td className="text-right tabular-nums">{item.quantity_on_hand}</td>
                <td className="text-right tabular-nums">{item.quantity_reserved}</td>
                <td className="text-right font-semibold tabular-nums">{item.available_quantity}</td>
                <td className="text-right tabular-nums">{item.reorder_point}</td>
                <td><StockStatus item={item} /></td>
              </tr>
            ))}
            {!filtered.length && (
              <tr>
                <td colSpan={8}>
                  <EmptyState title="No inventory matches" detail="Try a different search or filter." />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ImportPage({ lastImport, onImported }: { lastImport: ImportSummary | null; onImported: (summary: ImportSummary) => Promise<void> }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const supported = [".xlsx", ".xls"];
  const chooseFile = (candidate: File | undefined) => {
    setError("");
    if (!candidate) return;
    if (!supported.includes(candidate.name.slice(candidate.name.lastIndexOf(".")).toLowerCase())) {
      setFile(null);
      setError("Choose an Excel workbook in .xlsx or .xls format.");
      return;
    }
    setFile(candidate);
  };
  const submit = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      await onImported(await api.importInventory(file));
      setFile(null);
      if (inputRef.current) inputRef.current.value = "";
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The inventory import could not be completed.");
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="grid w-full max-w-full grid-cols-1 gap-7 xl:grid-cols-[1fr_.8fr]">
      <section className="panel w-full min-w-0">
        <div className="mb-6">
          <h2 className="section-title">Upload an inventory workbook</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-[#5c6d66]">The backend validates the workbook, matches component part numbers, and records only real quantity changes. Your current inventory is never blindly replaced.</p>
        </div>
        <div
          className={`dropzone ${dragging ? "dropzone-active" : ""}`}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0]); }}
        >
          <div className="upload-icon" aria-hidden="true">↑</div>
          <p className="font-semibold text-[#1c2d27]">Drop your Excel file here</p>
          <p className="mt-1 text-sm text-[#7c8b84]">or choose a file from your computer</p>
          <input ref={inputRef} className="sr-only" id="excel-file" type="file" accept=".xlsx,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/vnd.ms-excel" onChange={(event) => chooseFile(event.target.files?.[0])} />
          <button className="button-secondary mt-5" onClick={() => inputRef.current?.click()}>Choose Excel file</button>
          <p className="mt-4 text-xs text-[#8b9992]">Supported formats: .xlsx and .xls</p>
        </div>
        {file && (
          <div className="selected-file">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">{file.name}</p>
              <p className="mt-1 text-xs text-[#7c8b84]">{(file.size / 1024).toFixed(1)} KB · ready to import</p>
            </div>
            <button className="icon-button" aria-label="Remove selected file" title="Remove selected file" onClick={() => { setFile(null); if (inputRef.current) inputRef.current.value = ""; }}>×</button>
          </div>
        )}
        {error && <div className="alert-error mt-4" role="alert">{error}</div>}
        <button className="button-primary mt-5 w-full justify-center sm:w-auto" disabled={!file || busy} onClick={() => void submit()}>
          {busy ? (<><span className="spinner spinner-light" /> Processing workbook...</>) : (<>Import inventory <span aria-hidden="true">→</span></>)}
        </button>
      </section>
      <section className="panel w-full min-w-0">
        <PanelHeading title="Latest result" detail="The import summary appears here after processing." />
        {lastImport ? <ImportResult summary={lastImport} /> : <EmptyState title="Ready when you are" detail="No workbook has been imported in this session." />}
      </section>
    </div>
  );
}
function ImportResult({ summary }: { summary: ImportSummary }) {
  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-[.1em] text-[#7c8b84]">Import completed</p>
          <h3 className="mt-1 break-all text-lg font-bold text-[#1a4d3f]">{summary.filename}</h3>
        </div>
        <span className="status-pill status-green shrink-0">{summary.status}</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <ResultStat label="Rows processed" value={summary.rows_processed} />
        <ResultStat label="New components" value={summary.new_components} />
        <ResultStat label="Updated" value={summary.updated_components} />
        <ResultStat label="Unchanged" value={summary.unchanged_components} />
      </div>
      {(summary.invalid_rows || summary.unmatched_rows || summary.low_stock_components) > 0 && (
        <div className="space-y-2 rounded-xl border border-[#f3dfb8] bg-[#fef3e2] p-4 text-sm text-[#8a5209]">
          <p className="font-semibold">Items needing attention</p>
          {summary.low_stock_components > 0 && <p>⚠ {summary.low_stock_components} component{summary.low_stock_components === 1 ? "" : "s"} require reorder.</p>}
          {summary.invalid_rows > 0 && <p>⚠ {summary.invalid_rows} row{summary.invalid_rows === 1 ? "" : "s"} could not be imported.</p>}
          {summary.unmatched_rows > 0 && <p>⚠ {summary.unmatched_rows} row{summary.unmatched_rows === 1 ? "" : "s"} could not be matched.</p>}
        </div>
      )}
      {summary.flagged_matches.length > 0 && (
        <div className="space-y-2 rounded-xl border border-[#bcd6ef] bg-[#e8f0fa] p-4 text-sm text-[#0d4a87]">
          <p className="font-semibold">Possible formatting duplicates — please confirm</p>
          <p className="text-[#2c5c8c]">These rows matched an existing component only after ignoring punctuation/case. Confirm they're really the same part.</p>
          <ul className="list-disc space-y-1 pl-5">
            {summary.flagged_matches.map((match) => (<li key={match}>{match}</li>))}
          </ul>
        </div>
      )}
      {summary.invalid_details.length > 0 && (
        <details className="text-sm text-[#5c6d66]">
          <summary className="cursor-pointer font-semibold">Show validation details</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {summary.invalid_details.map((detail) => (<li key={detail}>{detail}</li>))}
          </ul>
        </details>
      )}
    </div>
  );
}
function ResultStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg bg-[#f7faf8] p-3">
      <p className="text-xs text-[#7c8b84]">{label}</p>
      <p className="mt-1 text-xl font-bold text-[#1a4d3f]">{value}</p>
    </div>
  );
}

