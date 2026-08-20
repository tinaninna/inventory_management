export type View = "dashboard" | "inventory" | "import" | "projects" | "reports";

export interface InventoryItem { id: number; component_id: number; manufacturer_part_number: string; description: string | null; value: string | null; manufacturer: string | null; quantity_on_hand: number; quantity_reserved: number; available_quantity: number; reorder_point: number; requires_reorder: boolean; }
export interface ImportJob { id: number; filename: string; status: string; started_at: string | null; completed_at: string | null; rows_processed: number; new_components: number; updated_components: number; unchanged_components: number; invalid_rows: number; unmatched_rows: number; summary: string | null; }
export interface ImportSummary { status: string; import_job_id: number; filename: string; rows_processed: number; new_components: number; updated_components: number; unchanged_components: number; invalid_rows: number; unmatched_rows: number; invalid_details: string[]; low_stock_components: number; }
export interface LegacyDashboard { component_count: number; project_count: number; bom_item_count: number; projects: LegacyProjectSummary[]; }
export interface LegacyProjectSummary { id: number; name: string; component_count: number; total_quantity_required: number; }
export interface LegacyProject { id: number; name: string; }
export interface BomItem { id: number; component_id: number; manufacturer_part_number: string; description: string | null; value: string | null; manufacturer: string | null; quantity_required: number; reference_designators: string | null; }
export interface BuildLine { component_id: number; manufacturer_part_number: string; required_quantity: number; previous_available_quantity: number; consumed_quantity: number; remaining_available_quantity: number; shortage_quantity: number; }
export interface BuildResult { project: { id: number; name: string }; build_quantity: number; success: boolean; build_id: number | null; required_components: BuildLine[]; shortages: BuildLine[]; }
export interface BuildHistoryItem { id: number; project_id: number; build_quantity: number; status: string; notes: string | null; created_at: string; }