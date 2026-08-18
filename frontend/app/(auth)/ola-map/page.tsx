"use client";

import { useEffect, useState } from "react";
import { Store, Package } from "lucide-react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";

type Errors = {
  [key: string]: string;
};

export default function StoreForm() {

    const [form, setForm] = useState({
    storeType: "",
    productId:"",
    
  });


  
    const [errors, setErrors] = useState<Errors>({});
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

    const handleChange = (key: string, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: "" }));
    }
  };

  /* ------------------ API CALL FOR PRODUCTS ------------------ */
  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        const res = await fetch("api/product-type"); // your API
        const data = await res.json();
        setProducts(data);
      } catch (error) {
        console.error("Failed to fetch products");
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []);

  return (
    <DashboardLayout>
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

      {/* -------- STORE TYPE -------- */}
      <div className="space-y-2">
        <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Store size={16} className="text-pink-500" />
          Store Type
          <span className="text-red-400">*</span>
        </label>

        <div className="relative">
          <select
            value={form.storeType}
            onChange={(e) => handleChange("storeType", e.target.value)}
            className={`w-full appearance-none px-4 py-3 pr-10 rounded-xl text-sm bg-white
            border transition-all
            ${
              errors.storeType
                ? "border-red-400 focus:ring-red-400"
                : "border-gray-200 focus:ring-pink-400"
            }
            focus:ring-2 focus:outline-none`}
          >
            <option value="">Choose Store Type</option>
            <option value="ONLINE">ONLINE</option>
            <option value="OFFLINE">OFFLINE</option>
            <option value="BOTH">BOTH</option>
          </select>

          {/* Dropdown Arrow */}
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
            ▼
          </span>
        </div>

        {errors.storeType && (
          <p className="text-xs text-red-400">{errors.storeType}</p>
        )}
      </div>

      {/* -------- PRODUCTS -------- */}
      <div className="space-y-2">
        <label className="text-sm font-semibold text-gray-700 flex items-center gap-2">
          <Package size={16} className="text-pink-500" />
          Add Products
          <span className="text-red-400">*</span>
        </label>

        <div className="relative">
          <select
            value={form.productId}
            disabled={loading}
            onChange={(e) => handleChange("productId", e.target.value)}
            className={`w-full appearance-none px-4 py-3 pr-10 rounded-xl text-sm bg-white
            border transition-all
            ${
              errors.productId
                ? "border-red-400 focus:ring-red-400"
                : "border-gray-200 focus:ring-pink-400"
            }
            disabled:bg-gray-100 disabled:cursor-not-allowed
            focus:ring-2 focus:outline-none`}
          >
            <option value="">
              {loading ? "Loading products..." : "Choose Product"}
            </option>

            {products.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>

          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-gray-400">
            ▼
          </span>
        </div>

        {errors.productId && (
          <p className="text-xs text-red-400">{errors.productId}</p>
        )}
      </div>
    </div>
    </DashboardLayout>
  );
}
