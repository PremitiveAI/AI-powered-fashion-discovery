"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { Search, Pencil, Trash2, Mail, ChevronLeft, ChevronRight, } from "lucide-react";
import Toast from "@/app/components/toast";
import { Loader } from "@/app/components/loader";

/* ---------- Types ---------- */
interface Store {
  id: number;
  name: string;
  type: "Online" | "Offline";
  address: string;
  city: string;
  state: string;
  contact: string;
  email: string;
}

type SortKey = "name" | "city" | "type" | "address" | "contact" | "email";
type SortOrder = "asc" | "desc";

export default function StoreListPage() {
  const router = useRouter();

  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(5);
  const [sortKey, setSortKey] = useState<keyof Store>("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [id, setId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const showToast = (message: string, type: "success" | "error") => {
    setToastMessage(message);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  /* ---------- API CALL ---------- */
  useEffect(() => {
    const fetchStores = async () => {
      try {
        setLoading(true);

        const res = await fetch("/api/store-list", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            products_id: [],
            latitude: 0,
            longitude: 0,
          }),
        });

        const json = await res.json();

        const apiStores: Store[] = (json?.data || []).map((item: any) => ({
          id: item.id,
          name: item.store_name,
          type: item.store_type === "ONLINE" ? "Online" : "Offline",
          address: item.address || "-",
          city: item.city || "-",
          state: item.state || "-",
          contact: item.phone || "-",
          email: item.email || null,
        }));

        setStores(apiStores);
      } catch (err) {
        console.error("Failed to load stores", err);
      } finally {
        setLoading(false);
      }
    };

    fetchStores();
  }, []);

  /* ---------- DELETE HANDLER ---------- */

  const confirmDelete = async () => {
    if (!id) return;

    try {
      setIsDeleting(true);

      const res = await fetch(`/api/store-delete/${id}`, {
        method: "DELETE",
      });

      const json = await res.json();

      if (!res.ok) {
        throw new Error(json?.message || "Delete failed");
      }

      // Remove deleted store from UI
      setStores((prev) => prev.filter((s) => s.id !== id));
      setId(null);
      toastMessage && setToastMessage("Store deleted successfully");
    } catch (error) {
      console.error(error);
      alert("Failed to delete store");
    } finally {
      setIsDeleting(false);
    }
  };


  /* ---------- SEARCH + SORT ---------- */
  const filteredStores = useMemo(() => {
    let data = [...stores];

    if (search) {
      const q = search.toLowerCase();
      data = data.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.city.toLowerCase().includes(q) ||
          s.type.toLowerCase().includes(q)
      );
    }

    data.sort((a, b) => {
      const aVal = a[sortKey].toString().toLowerCase();
      const bVal = b[sortKey].toString().toLowerCase();

      if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
      if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });

    return data;
  }, [stores, search, sortKey, sortOrder]);

  /* ---------- Pagination ---------- */
  const totalPages = Math.max(
    1,
    Math.ceil(filteredStores.length / pageSize)
  );

  const paginatedStores = filteredStores.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const handlePrev = () => page > 1 && setPage(page - 1);
  const handleNext = () => page < totalPages && setPage(page + 1);

  /* ---------- SORT HANDLER ---------- */
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  };

  return (
<DashboardLayout>
  <div className="w-full bg-[#252525B2] h-full p-4 sm:p-8 flex flex-col">
    {/* Toast */}
    {toastMessage && toastType && (
      <Toast message={toastMessage} type={toastType} />
    )}

    {/* ================= HEADER ================= */}
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-300 tracking-tight">
          Store List
        </h1>
        <p className="text-sm text-gray-400 mt-1">
          Manage all Stores
        </p>
      </div>
    </div>

    {/* ================= SEARCH + ACTION ================= */}
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
      <div className="relative w-full sm:max-w-md">
        <Search
          size={18}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
        />
        <input
          type="text"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          placeholder="Search by store name or city"
          className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-700
                     focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[#1C1B1B]
                     text-sm text-gray-300 placeholder:text-gray-400"
        />
      </div>

      <button
        onClick={() => router.push("/add-store")}
        className="px-8 py-2 rounded-xl bg-[linear-gradient(90deg,rgba(41,32,195,0.9)_8.65%,rgba(79,70,229,0.9)_37.98%,rgba(37,99,235,0.9)_100%)]
                    text-white font-semibold hover:brightness-105 transition"
      >
        Add Store
      </button>
    </div>

    {/* ================= DESKTOP TABLE ================= */}
    <div className="hidden lg:flex flex-col bg-[#252525B2] rounded-3xl shadow-sm border border-gray-600 overflow-hidden flex-1">
      <div className="overflow-y-auto flex-1 relative">
            {/* Loader */}
            {loading && (
              <div className="absolute inset-0 bg-[#1C1B1B] flex items-center justify-center z-10">
                <Loader size="lg" />
              </div>
            )}
        <table className="w-full border-collapse">
          <thead className="sticky top-0 z-10 bg-gray-800/80 backdrop-blur-sm">
            <tr className=" text-left text-[13px] font-medium text-gray-300 border-b border-gray-700">
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("name")}>Store Name</th>
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("type")}>Type</th>
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("address")}>Address</th>
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("city")}>City / State</th>
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("contact")}>Contact</th>
              <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("email")}>Email</th>
              <th className="px-6 py-5 text-center">Actions</th>
            </tr>
          </thead>

          <tbody className="divide-y divide-gray-700">
            {loading ? null : paginatedStores.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-20 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <div className="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center">
                      <Search size={22} className="text-gray-500" />
                    </div>

                    <h3 className="text-lg font-semibold text-gray-300">
                      No Stores Found
                    </h3>

                    <p className="text-sm text-gray-500">
                      Try adjusting your search or add a new store.
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              paginatedStores.map((store) => (
                <tr key={store.id} className="hover:bg-gray-800 transition-colors">
                  <td className="px-6 py-5 font-bold text-gray-300">
                    {store.name}
                  </td>

                  <td className="px-6 py-5">
                    <span
                      className={`px-4 py-1 rounded-full text-xs font-medium
                        ${
                          store.type === "Online"
                            ? "bg-[#E8F0FE] text-[#1A73E8]"
                            : "bg-gray-400 text-gray-800"
                        }`}
                    >
                      {store.type}
                    </span>
                  </td>

                  <td className="px-6 py-5 text-sm text-gray-400 truncate max-w-xs">
                    {store.address}
                  </td>

                  <td className="px-6 py-5">
                    <div className="font-medium text-gray-300">{store.city}</div>
                    <div className="text-xs text-gray-400">{store.state}</div>
                  </td>

                  <td className="px-6 py-5 text-sm text-gray-400">
                    {store.contact}
                  </td>

                  <td className="px-6 py-5 text-sm text-gray-400">
                    {store.email || "-"}
                  </td>

                  <td className="px-6 py-5 text-right pr-6">
                    <div className="flex justify-end gap-4">
                      <Pencil
                        size={18}
                        className="cursor-pointer text-gray-400 hover:text-blue-600"
                        onClick={() =>
                          router.push(
                            `/add-store?id=${encodeURIComponent(store.id)}`
                          )
                        }
                      />
                      <Trash2
                        size={18}
                        className="cursor-pointer text-gray-400 hover:text-red-600"
                        onClick={() => setId(store.id)}
                      />
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>

    {/* ================= MOBILE / TABLET CARD VIEW ================= */}
    <div className="lg:hidden relative grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto flex-1">
      {loading && (
      <div className="absolute inset-0 bg-[#1C1B1B]/70 flex items-center justify-center z-10">
        <Loader size="lg" />
      </div>
      )}
      {paginatedStores.map((store) => (
        <div
          key={store.id}
          className="rounded-2xl shadow-sm border border-gray-700 p-4 flex flex-col gap-4"
        >
          <div className="flex justify-between items-start">
            <div>
              <h3 className="font-bold text-gray-300">{store.name}</h3>
              <p className="text-xs text-gray-400 mt-1">{store.address}</p>

            </div>

            <div className="flex gap-3">
              <Pencil
                size={18}
                className="text-gray-400 hover:text-blue-600"
                onClick={() => router.push(`/add-store?id=${encodeURIComponent(store.id)}`)}
              />
              <Trash2
                size={18}
                className="text-gray-400 hover:text-red-600"
                onClick={() => setId(store.id)}
              />
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            
            <span className="text-xs text-gray-500">
              {store.city}, {store.state}
            </span>
            <span className="px-3 py-1 rounded-full text-xs bg-[#E8F0FE] text-[#1A73E8]">
              {store.type}
            </span>
          </div>

          <div className="text-sm text-gray-400">
            <div>{store.contact}</div>
            <div>{store.email || "-"}</div>
          </div>
        </div>
      ))}
    </div>

    {/* ================= PAGINATION ================= */}
    <div className="mt-4 flex flex-col sm:flex-row items-center justify-between
                    gap-4 px-2 sm:px-6 py-4 rounded-xl text-sm">
      <p className="text-gray-400">
        Showing {(page - 1) * pageSize + 1} –{" "}
        {Math.min(page * pageSize, filteredStores.length)} of{" "}
        {filteredStores.length}
      </p>

      <div className="flex items-center gap-3">
        <button
          onClick={handlePrev}
          disabled={page === 1}
          className="px-3 py-1.5 rounded-lg border text-gray-400
                     disabled:opacity-40 hover:bg-gray-700"
        >
          Prev
        </button>

        <span className="font-medium text-gray-400">
          Page {page} / {totalPages || 1}
        </span>

        <button
          onClick={handleNext}
          disabled={page === totalPages || totalPages === 0}
          className="px-3 py-1.5 rounded-lg border text-gray-400
                     disabled:opacity-40 hover:bg-gray-700"
        >
          Next
        </button>
      </div>
    </div>

    {/* ================= DELETE MODAL ================= */}
        <div
          className={`fixed inset-0 z-[999] flex items-center justify-center transition-all duration-300
    ${id ? "opacity-100 visible" : "opacity-0 invisible"}`}
        >
          {/* Modern Glass Backdrop */}
          <div
            className="absolute inset-0 bg-slate-950/40 backdrop-blur-md"
            onClick={() => !isDeleting && setId(null)}
          />

          {/* Modal Card */}
          <div
            className={`relative text-center w-[95%] max-w-md px-8 py-10 shadow-2xl rounded-3xl border border-white/10 
      bg-gradient-to-b from-purple-900/80 to-indigo-950/90 backdrop-blur-xl
      transform transition-all duration-300
      ${id ? "scale-100 translate-y-0" : "scale-90 translate-y-4"}`}
          >
            {/* Close Icon with Glow */}
            <button
              onClick={() => !isDeleting && setId(null)}
              className="absolute top-4 right-4 p-2 text-white/50 hover:text-white hover:bg-white/10 rounded-full transition-all"
              disabled={isDeleting}
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Danger Icon / Visual Element */}
            <div className="mx-auto mb-4 flex items-center justify-center w-16 h-16 rounded-full bg-red-500/10 border border-red-500/20">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </div>

            <h2 className="text-3xl font-extrabold text-white tracking-tight">
              Confirm Deletion
            </h2>

            <p className="text-purple-100/70 mt-3 text-lg leading-relaxed">
              Are you sure you want to delete this store?
              <span className="block text-red-400 text-sm font-semibold mt-2 uppercase tracking-widest">
                This action cannot be undone.
              </span>
            </p>

            <div className="flex flex-col sm:flex-row justify-center mt-8 gap-3">
              {/* Cancel Button - Subtle Glass Style */}
              <button
                onClick={() => setId(null)}
                disabled={isDeleting}
                className="order-2 sm:order-1 flex-1 px-6 py-3 rounded-2xl text-sm font-bold text-white 
                   bg-white/5 border border-white/10 hover:bg-white/10 
                   transition-all active:scale-95 disabled:opacity-50"
              >
                Keep Store
              </button>

              {/* Delete Button - Vibrant Red/Orange Gradient */}
              <button
                onClick={confirmDelete}
                disabled={isDeleting}
                className="order-1 sm:order-2 flex-1 px-6 py-3 rounded-2xl text-sm font-bold text-white
                   bg-gradient-to-r from-red-500 to-pink-600 hover:from-red-600 hover:to-pink-700
                   shadow-[0_0_20px_rgba(239,68,68,0.4)] hover:shadow-[0_0_25px_rgba(239,68,68,0.6)]
                   transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Deleting...
                  </>
                ) : (
                  "Delete Store"
                )}
              </button>
            </div>
          </div>
        </div>

  </div>
</DashboardLayout>

  );
}
