"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState, useEffect } from "react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { Search, Pencil, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import Toast from "@/app/components/toast";
import { Loader } from "@/app/components/loader";

/* ---------- Types ---------- */
interface Category {
  id: number;
  name: string;
}

interface Brand {
  id: number;
  name: string;
}

interface Color {
  id: number;
  name: string;
}

interface Product {
  id: number;
  name: string;
  description: string;
  category: Category | null;
  brands: Brand[];
  colors: Color[];
  price: number;
  mrp: number;
}

/* ---------- Component ---------- */
export default function ProductListPage() {
  const router = useRouter();

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);

  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(5);
  const [sortKey, setSortKey] = useState<keyof Product>("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [id, setId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error" | null>(null);

  /* ---------- API CALL ---------- */
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);

        const res = await fetch("/api/product-list", {
          method: "POST",
        });

        const json = await res.json();

        const apiProducts: Product[] = (json?.data || []).map((item: any) => ({
          id: item.id,
          name: item.name,
          description: item.description || "-",
          category: item.category || null,
          brands: item.brands || [],
          colors: item.colors || [],
          price: item.price || 0,
          mrp: item.mrp || 0,
        }));

        setProducts(apiProducts);
      } catch (err) {
        console.error("Failed to load products", err);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  /* ---------- DELETE HANDLER ---------- */
  const confirmDelete = async () => {
    if (!id) return;

    try {
      setIsDeleting(true);

      const res = await fetch(`/api/product-delete/${id}`, {
        method: "DELETE",
      });

      const json = await res.json();

      if (!res.ok) {
        throw new Error(json?.message || "Delete failed");
      }

      // Remove deleted product from UI
      setProducts((prev) => prev.filter((p) => p.id !== id));
      setId(null);
      setToastMessage("Product deleted successfully");
      setToastType("success");
    } catch (error) {
      console.error(error);
      setToastMessage("Failed to delete product");
      setToastType("error");
    } finally { setIsDeleting(false); }
  };

  /* ---------- SEARCH + SORT ---------- */
  const filteredProducts = useMemo(() => {
    let data = [...products];

    if (search) {
      const q = search.toLowerCase();
      data = data.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.brands.some((b) => b.name.toLowerCase().includes(q)) ||
          p.category?.name.toLowerCase().includes(q)
      );
    }

    data.sort((a, b) => {
      let aVal = "";
      let bVal = "";

      if (sortKey === "category") {
        aVal = a.category?.name.toLowerCase() ?? "";
        bVal = b.category?.name.toLowerCase() ?? "";
      } else if (sortKey === "brands") {
        aVal = a.brands[0]?.name.toLowerCase() ?? "";
        bVal = b.brands[0]?.name.toLowerCase() ?? "";
      } else if (sortKey === "colors") {
        aVal = a.colors[0]?.name.toLowerCase() ?? "";
        bVal = b.colors[0]?.name.toLowerCase() ?? "";
      } else {
        aVal = (a[sortKey] ?? "").toString().toLowerCase();
        bVal = (b[sortKey] ?? "").toString().toLowerCase();
      }

      if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
      if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });


    return data;
  }, [products, search, sortKey, sortOrder]);

  /* ---------- Pagination ---------- */
  const totalPages = Math.max(1, Math.ceil(filteredProducts.length / pageSize));

  const paginatedProducts = filteredProducts.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const handlePrev = () => page > 1 && setPage(page - 1);
  const handleNext = () => page < totalPages && setPage(page + 1);

  /* ---------- SORT HANDLER ---------- */
  const handleSort = (key: keyof Product) => {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortOrder("asc");
    }
  };
  return (
    <DashboardLayout>
      <div className="w-full h-full p-4 sm:p-8 flex flex-col bg-[#1C1B1B]">
        {/* Toast Notification */}
        {toastMessage && toastType && (
          <Toast message={toastMessage} type={toastType} />
        )}

        {/* ================= HEADER ================= */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-200 tracking-tight">
              Product List
            </h1>
            <p className="text-sm text-gray-400 mt-1">
              Manage all Products
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
              placeholder="Search by product name, brand or category"
              className="w-full pl-11 pr-4 py-3 rounded-xl border border-gray-700
                     focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[#1C1B1B]
                     text-sm text-gray-300 placeholder:text-gray-400"
            />
          </div>

          <button
            onClick={() => router.push("/add-product")}
            className="px-8 py-2 rounded-xl bg-[linear-gradient(90deg,rgba(41,32,195,0.9)_8.65%,rgba(79,70,229,0.9)_37.98%,rgba(37,99,235,0.9)_100%)]
                    text-white font-semibold hover:brightness-105 transition"
          >
            Add Product
          </button>
        </div>

        {/* ================= DESKTOP TABLE (SCROLL AREA) ================= */}
        <div className="hidden lg:flex flex-col  border border-gray-700 rounded-3xl shadow-sm overflow-hidden flex-1">
          {/* TABLE SCROLL CONTAINER */}
          <div className="overflow-y-auto flex-1 relative">
            {/* Loader */}
            {loading && (
              <div className="absolute inset-0 bg-[#1C1B1B] flex items-center justify-center z-10">
                <Loader size="lg" />
              </div>
            )}
            <table className="w-full border-collapse">
              <thead className="sticky top-0 z-10 bg-gray-500">
                <tr className="text-left font-medium text-gray-300 bg-gray-800 border-b border-gray-700">
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("name")}>Product Name</th>
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("category")}>Category</th>
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("brands")}>Brand</th>
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("colors")}>Colour</th>
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("price")}>Price</th>
                  <th className="px-6 py-5 cursor-pointer" onClick={() => handleSort("mrp")}>MRP</th>
                  <th className="px-6 py-5 text-center">Actions</th>
                </tr>
              </thead>

            <tbody className="divide-y divide-gray-700">
              {loading ? null : paginatedProducts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-20 text-center">
                    <div className="flex flex-col items-center justify-center gap-3">
                      <div className="w-14 h-14 rounded-full bg-gray-800 flex items-center justify-center">
                        <Search size={22} className="text-gray-500" />
                      </div>

                      <h3 className="text-lg font-semibold text-gray-300">
                        No Products Found
                      </h3>

                      <p className="text-sm text-gray-500">
                        Try adjusting your search or add a new product.
                      </p>
                    </div>
                  </td>
                </tr>
              ) : (
                paginatedProducts.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-800 transition-colors">
                    <td className="px-6 py-5">
                      <span className="font-bold text-gray-300 block">
                        {product.name}
                      </span>
                      <span className="text-xs text-gray-400 block mt-1 line-clamp-1 truncate max-w-xs">
                        {product.description}
                      </span>
                    </td>

                    <td className="px-6 py-5">
                      <span className="px-4 py-1 rounded-full text-xs font-medium bg-[#E8F0FE] text-[#1A73E8]">
                        {product.category?.name}
                      </span>
                    </td>

                    <td className="px-6 py-5 text-sm text-gray-300">
                      {product.brands.map((b) => b.name).join(", ")}
                    </td>

                    <td className="px-6 py-5 text-sm text-gray-300">
                      {product.colors.map((c) => c.name).join(", ")}
                    </td>

                    <td className="px-6 py-5 font-bold text-[#2E7D32] text-sm">
                      ₹{product.price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>

                    <td className="px-6 py-5 text-gray-400 text-sm line-through">
                      ₹{product.mrp.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>

                    <td className="px-6 py-5 text-right pr-6">
                      <div className="flex justify-end gap-4">
                        <Pencil
                          size={18}
                          className="cursor-pointer text-gray-400 hover:text-blue-600"
                          onClick={() =>
                            router.push(`/add-product?id=${encodeURIComponent(product.id)}`)
                          }
                        />
                        <Trash2
                          size={18}
                          className="cursor-pointer text-gray-400 hover:text-red-600"
                          onClick={() => setId(product.id)}
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

        {/* ================= MOBILE + TABLET CARD VIEW ================= */}
        <div className="lg:hidden grid grid-cols-1 md:grid-cols-2 gap-4 overflow-y-auto flex-1">
          {paginatedProducts.map((product) => (
            <div
              key={product.id}
              className="rounded-2xl shadow-sm border border-gray-800 p-4 flex flex-col gap-4"
            >
              {/* HEADER */}
              <div className="flex justify-between items-start gap-3">
                <div>
                  <h3 className="font-bold text-gray-400 text-base">
                    {product.name}
                  </h3>
                  <p className="text-xs text-gray-400 mt-1 line-clamp-2 truncate max-w-xs">
                    {product.description}
                  </p>
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => router.push(`/add-product?id=${encodeURIComponent(product.id)}`)}
                    className="text-gray-400 hover:text-blue-600 transition"
                  >
                    <Pencil size={18} />
                  </button>

                  <button
                    onClick={() => setId(product.id)}
                    className="text-gray-400 hover:text-red-600 transition"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>

              {/* CATEGORY */}
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 rounded-full text-xs font-medium bg-[#E8F0FE] text-[#1A73E8]">
                  {product.category?.name}
                </span>
              </div>

              {/* BRAND */}
              <div>
                <p className="text-xs text-gray-400">Brand</p>
                <p className="text-sm text-gray-700 mt-1">
                  {product.brands.map((b) => b.name).join(", ")}
                </p>
              </div>

              {/* COLOUR */}
              <div>
                <p className="text-xs text-gray-400">Colour</p>
                <p className="text-sm text-gray-700 mt-1">
                  {product.colors.map((c) => c.name).join(", ")}
                </p>
              </div>

              {/* PRICE INFO */}
              <div className="flex items-end justify-between mt-2">
                <div>
                  <p className="text-xs text-gray-400">Price</p>
                  <p className="font-bold text-[#2E7D32] text-sm">
                    ₹{product.price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-xs text-gray-400">MRP</p>
                  <p className="text-sm text-gray-400 line-through">
                    ₹{product.mrp.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ================= PAGINATION ================= */}
        <div className="mt-4 flex flex-col sm:flex-row items-center justify-between
     gap-4 px-2 sm:px-6 py-4 rounded-xl text-sm">

          {/* INFO */}
          <p className="text-gray-300">
            Showing {(page - 1) * pageSize + 1} –{" "}
            {Math.min(page * pageSize, filteredProducts.length)} of{" "}
            {filteredProducts.length}
          </p>

          {/* CONTROLS */}
          <div className="flex items-center gap-3">
            <button
              onClick={handlePrev}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg border text-gray-400
           disabled:opacity-40 disabled:cursor-not-allowed
            transition"
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
           disabled:opacity-40 disabled:cursor-not-allowed
           transition"
            >
              Next
            </button>
          </div>
        </div>

      {/* ================= DELETE CONFIRMATION MODAL ================= */}
<div
  className={`fixed inset-0 z-[100] flex items-center justify-center
    transition-all duration-200
    ${id ? "opacity-100 visible" : "opacity-0 invisible"}`}
>
  {/* BACKDROP */}
  <div
    className="absolute inset-0 bg-black/60 backdrop-blur-sm"
    onClick={() => !isDeleting && setId(null)}
  />

  {/* MODAL */}
  <div
    className={`relative bg-white w-[90%] max-w-md rounded-2xl shadow-2xl p-6
      transform transition-all duration-200
      ${id ? "scale-100 translate-y-0" : "scale-95 translate-y-2"}`}
  >
    <h2 className="text-xl font-bold text-gray-200 mb-3">
      Confirm Deletion
    </h2>

    <p className="text-sm text-gray-600 mb-6 leading-relaxed">
      Are you sure you want to delete this product?
      <br />
      <span className="text-red-500 font-medium">
        This action cannot be undone.
      </span>
    </p>

    <div className="flex justify-end gap-3">
      <button
        onClick={() => setId(null)}
        disabled={isDeleting}
        className="px-4 py-2 rounded-xl text-sm font-medium
          text-gray-700 bg-gray-100 hover:bg-gray-200
          transition disabled:opacity-50"
      >
        Cancel
      </button>

      <button
        onClick={confirmDelete}
        disabled={isDeleting}
        className="px-4 py-2 rounded-xl text-sm font-semibold text-white
          bg-red-600 hover:bg-red-700 transition
          disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isDeleting ? "Deleting..." : "Delete"}
      </button>
    </div>
  </div>
</div>

      </div>
    </DashboardLayout>
  );
}