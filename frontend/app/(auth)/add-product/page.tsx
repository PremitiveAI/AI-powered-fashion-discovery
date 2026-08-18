"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { UploadCloud, X } from "lucide-react";
import { ChevronDownIcon } from "@heroicons/react/24/outline";
import { useRef } from "react";
import { ArrowLeft } from "lucide-react";
import Toast from "@/app/components/toast";

interface ProductImage {
  id: number;
  preview: string;
  file: File;
  uploadedId: number;
}


const DUMMY_GENDER = ["Male", "Female"];

const createProductAPI = async (payload: any) => {
  console.log("Submitting payload to API:", payload);
  return new Promise((resolve) => setTimeout(resolve, 1000));
};

type Errors = {
  [key: string]: string;
};

export default function AddProductPage() {

  const [form, setForm] = useState({
    productName: "",
    category: "",
    subType: "",
    pattern: "",
    brand: [] as string[],   // ✅ MULTI
    description: "",
    price: "",
    mrp: "",
    colour: [] as string[],  // ✅ MULTI
    gender: "",
  });


  const hasFetchedMasters = useRef(false);
  const hasFetchedProduct = useRef(false);
  const [errors, setErrors] = useState<Errors>({});
  const [images, setImages] = useState<ProductImage[]>([]);
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const searchParams = useSearchParams();
    const id = searchParams.get("id");
 const isEdit = Boolean(id);

  const [genderOpen, setGenderOpen] = useState(false);
  const genderRef = useRef<HTMLDivElement>(null);

  const [categories, setCategories] = useState<any[]>([]);
  const [categoryLoading, setCategoryLoading] = useState(false);
  const [categoryOpen, setCategoryOpen] = useState(false);
  const categoryRef = useRef<HTMLDivElement>(null);

  const [brands, setBrands] = useState<any[]>([]);
  const [brandLoading, setBrandLoading] = useState(false);
  const [brandOpen, setBrandOpen] = useState(false);
  const [brandSearchTerm, setBrandSearchTerm] = useState("");
  const brandRef = useRef<HTMLDivElement>(null);

  const [colourOpen, setColourOpen] = useState(false);
  const [colourSearchTerm, setColourSearchTerm] = useState("");
  const [colours, setColours] = useState<any[]>([]);
  const [colourLoading, setColourLoading] = useState(false);
  const colourRef = useRef<HTMLDivElement>(null);
  const [toastMessage, showToast] = useState("");
  const [toastType, showToastType] = useState<"success" | "error">("success");

  const [subTypes, setSubTypes] = useState<any[]>([]);
  const [subTypeLoading, setSubTypeLoading] = useState(false);
  const [subTypeOpen, setSubTypeOpen] = useState(false);
  const subTypeRef = useRef<HTMLDivElement>(null);

  const [patterns, setPatterns] = useState<any[]>([]);
  const [patternLoading, setPatternLoading] = useState(false);
  const [patternOpen, setPatternOpen] = useState(false);
  const patternRef = useRef<HTMLDivElement>(null);

  const getItemsByIds = (
    ids: string[],
    options: { value: string; label: string }[]
  ) => {
    return options.filter((opt) => ids.includes(opt.value));
  };



  const fetchCategoryMaster = async () => {
    try {
      setCategoryLoading(true);
      const res = await fetch("/api/master/category-list", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          search: "",
          filter: "",
          sort: "createdAt",
          order: "DESC",
          limit: 100,
          offset: 0,
        }),
      });
      const data = await res.json();

      setCategories(
        (data?.Success?.data?.list || []).map((c: any) => ({
          id: String(c.id), // Force String
          name: c.name ?? c.category_name,
        }))
      );
    } catch (error) { console.error(error); } finally { setCategoryLoading(false); }
  };

  const fetchBrandMaster = async () => {
    try {
      setBrandLoading(true);

      const res = await fetch("/api/master/brand-list", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          search: "",
          filter: "",
          sort: "createdAt",
          order: "DESC",
          limit: 100,
          offset: 0,
        }),
      });

      const data = await res.json();
      console.log("🟢 Brand API:", data);

      setBrands(
        (data?.Success?.data?.list || []).map((b: any) => ({
          ...b,
          id: String(b.id),
        }))
      );

    } catch (error) {
      console.error("❌ Brand API error:", error);
    } finally {
      setBrandLoading(false);
    }
  };

  const fetchSubTypeMaster = async () => {
    try {
      setSubTypeLoading(true);

      const res = await fetch("/api/master/sub-type", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search: "",
          filter: "",
          sort: "createdAt",
          order: "DESC",
          limit: 100,
          offset: 0,
        }),
      });

      if (!res.ok) throw new Error("SubType API failed");

      const data = await res.json();

      setSubTypes(
        (data?.Success?.data?.list ?? []).map((s: any) => ({
          id: String(s.id),
          name: s.name,
        }))
      );
    } catch (error) {
      console.error("❌ SubType API error:", error);
      setSubTypes([]);
    } finally {
      setSubTypeLoading(false);
    }
  };

  const fetchPatternMaster = async () => {
  try {
    setPatternLoading(true);

    const res = await fetch("/api/master/pattern", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        search: "",
        filter: "",
        sort: "createdAt",
        order: "DESC",
        limit: 100,
        offset: 0,
      }),
    });

    if (!res.ok) throw new Error("Pattern API failed");

    const data = await res.json();

    setPatterns(
      (data?.Success?.data?.list ?? []).map((p: any) => ({
        id: String(p.id),
        name: p.name,
        type: p.type,
      }))
    );
  } catch (error) {
    console.error("❌ Pattern API error:", error);
    setPatterns([]);
  } finally {
    setPatternLoading(false);
  }
  };

  const fetchColourMaster = async () => {
    try {
      setColourLoading(true);

      const res = await fetch("/api/master/color-list", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          search: "",
          filter: "",
          sort: "createdAt",
          order: "DESC",
          limit: 100,
          offset: 0,
        }),
      });

      const data = await res.json();
      console.log("🟢 Colour API:", data);

      setColours(
        (data?.Success?.data?.list || []).map((c: any) => ({
          ...c,
          id: String(c.id),
        }))
      );

    } catch (error) {
      console.error("❌ Colour API error:", error);
    } finally {
      setColourLoading(false);
    }
  };

  const fetchProductById = async (id: string) => {
    try {
      setLoading(true);

      const res = await fetch(`/api/product-details/${encodeURIComponent(id)}`);
      const data = await res.json();
      const product = data?.Success?.data;
      if (!product) return;

      setForm({
        productName: product.name || "",

        // ✅ FIXED: category object → id
        category: product.category?.id
          ? String(product.category.id)
          : "",

        // ✅ FIXED: brands[] → ids
        brand: Array.isArray(product.brands)
          ? product.brands.map((b: any) => String(b.id))
          : [],

        subType:
        product.subtype_id
          ? String(product.subtype_id)
          : product.subtype?.id
          ? String(product.subtype.id)
          : "",

        pattern:
          product.pattern_id
            ? String(product.pattern_id)
            : product.pattern?.id
            ? String(product.pattern.id)
            : "",

        description: product.description || "",
        price: String(product.price || ""),
        mrp: String(product.mrp || ""),

        // ✅ FIXED: colors[] → ids
        colour: Array.isArray(product.colors)
          ? product.colors.map((c: any) => String(c.id))
          : [],

        gender: product.gender
          ? product.gender.charAt(0).toUpperCase() + product.gender.slice(1)
          : "",
      });

      // ✅ FIXED: set existing images in edit
      if (Array.isArray(product.images)) {
        setImages(
          product.images.map((img: any) => ({
            id: img.id,
            uploadedId: img.id,
            preview: img.path,
            file: null as any,
          }))
        );
      }
    } catch (error) {
      console.error("❌ Fetch product error:", error);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    if (!isEdit) return;
    if (!form.category) return;
    // trigger re-render safely
    setForm((prev) => ({ ...prev }));
  }, [categories]);


  useEffect(() => {
    if (hasFetchedMasters.current) return;

    hasFetchedMasters.current = true;

    fetchCategoryMaster();
    fetchBrandMaster();
    fetchColourMaster();
    fetchSubTypeMaster();
    fetchPatternMaster();
  }, []);


  useEffect(() => {
    if (!id) return;

    // ✅ wait until all master data is loaded
    if (
      categories.length === 0 ||
      brands.length === 0 ||
      colours.length === 0
    ) {
      return;
    }

    if (hasFetchedProduct.current) return;

    hasFetchedProduct.current = true;
    fetchProductById(id);
  }, [id, categories, brands, colours]);

  const uploadImage = async (file: File) => {
    const formData = new FormData();
    formData.append("files", file);

    const res = await fetch("/api/image-upload", {
      method: "POST",
      body: formData,
    });

    console.log("🟡 Upload status:", res.status);

    const text = await res.text();
    console.log("🟡 RAW UPLOAD RESPONSE:", text);

    // ✅ If backend returns nothing (most upload APIs do)
    if (!text) {
      console.log("🟢 Upload succeeded (no JSON returned)");
      return { success: true };
    }

    // ✅ Parse only if JSON exists
    try {
      return JSON.parse(text);
    } catch {
      throw new Error("Upload response is not valid JSON");
    }
  };


  const handleImageUpload = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);

    try {
      const uploadRes = await uploadImage(file);
      console.log("✅ Uploaded image response:", uploadRes);

      // ✅ extract backend image id
      const uploadedId =
        uploadRes?.Success?.data?.results?.[0]?.id;

      if (!uploadedId) {
        throw new Error("Image ID not returned from upload API");
      }

      setImages([
        {
          id: Date.now(), // frontend key
          file,
          preview: URL.createObjectURL(file),
          uploadedId, // ✅ REAL backend image id (e.g. 3)
        },
      ]);
    } catch (err) {
      console.error("❌ Upload failed:", err);
      alert("Image upload failed");
    } finally {
      setLoading(false);
    }
  };


  const handleDrop = async (e: React.DragEvent<HTMLLabelElement>) => {
  e.preventDefault();
  setIsDragging(false);

  const file = e.dataTransfer.files?.[0];
  if (!file) return;

  setLoading(true);

  try {
    const uploadRes = await uploadImage(file);

    const uploadedId =
      uploadRes?.Success?.data?.results?.[0]?.id;

    if (!uploadedId) {
      throw new Error("Image ID not returned from upload API");
    }

    setImages([
      {
        id: Date.now(),
        file,
        preview: URL.createObjectURL(file),
        uploadedId,
      },
    ]);
  } catch (err) {
    console.error("❌ Drag-drop upload failed:", err);
    showToast("Image Upload Failed");
    showToastType("error");
  } finally {
    setLoading(false);
  }
};


  const removeImage = (id: number) => {
    setImages((prev) => prev.filter((img) => img.id !== id));
  };

  const handleChange = (
    key: string,
    value: string | string[]
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors((prev) => ({ ...prev, [key]: "" }));
    }
  };

  const validateForm = () => {
    const newErrors: Errors = {};

    if (!form.productName.trim()) newErrors.productName = "Required";
    if (!form.category) newErrors.category = "Required";
    // if (!form.subType) newErrors.subType = "Required";   
    // if (!form.pattern) newErrors.pattern = "Required"; 
    if (form.brand.length < 1) newErrors.brand = "Select at least one brand";
    if (form.colour.length < 1) newErrors.colour = "Select at least one colour";
    if (!form.price) newErrors.price = "Required";
    if (!form.mrp) newErrors.mrp = "Required";
    if (!form.gender) newErrors.gender = "Required";

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    if (images.length === 0) {
      alert("Please upload product image");
      return;
    }

    try {
      setLoading(true);

      const res = await fetch("/api/product-add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: isEdit ? Number(id) : 0,
        hsn_code: "",
        product_code: "",
        name: form.productName,
        price: Number(form.price),
        mrp: Number(form.mrp),
        subtype_id: Number(form.subType),
        pattern_id: Number(form.pattern),
        category_id: Number(form.category),
        gender: form.gender.toLowerCase(),
        brand_id: form.brand.map(Number),
        color_id: form.colour.map(Number),

        // ✅ REAL IMAGE IDS FROM UPLOAD API
        images: images.map((img) => img.uploadedId),

        product_intro: "",
        description: form.description,
        specification: "",
        status: 1,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        showToast("Product added successfully");
      showToastType("success");
      router.push("/product-list");
      }else {
        showToast(data?.Error?.message || "Something went wrong");
      }
    } catch (err) {
      showToast("Server error");
    } finally {
      setLoading(false);
    }
  };
  
  const handleClear = () => {
    setForm({
      productName: "",
      category: "",
      brand: [],     // ✅ reset multiselect
      subType: "",
      pattern: "",
      description: "",
      price: "",
      mrp: "",
      colour: [],    // ✅ reset multiselect
      gender: "",
    });
    setImages([]);
    setErrors({})
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (categoryRef.current && !categoryRef.current.contains(event.target as Node)) {
        setCategoryOpen(false);
      }

      if (brandRef.current && !brandRef.current.contains(event.target as Node)) {
        setBrandOpen(false);
      }

      if (colourRef.current && !colourRef.current.contains(event.target as Node)) {
        setColourOpen(false);
      }

      if (genderRef.current && !genderRef.current.contains(event.target as Node)) {
        setGenderOpen(false);
      }
      if (subTypeRef.current && !subTypeRef.current.contains(event.target as Node)) {
      setSubTypeOpen(false);
      }
      if (patternRef.current && !patternRef.current.contains(event.target as Node)) {
        setPatternOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);
  
  return (
    <DashboardLayout>
      {isEdit && (
        <button
          onClick={() => router.back()}
          className="flex items-center gap-2 text-xl sm:text-xl lg:text-2xl
                            font-bold text-gray-200 px-2"
        >
          <ArrowLeft className="w-6 h-6 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
          <span>Back</span>
        </button>
      )}
      {/* Toast Notification */}
      {toastMessage && toastType && (
        <Toast message={toastMessage} type={toastType} />
      )}
      <div className="bg-[#1C1B1B] w-full px-4 sm:px-6 lg:px-8 h-full">
        <div className="max-w-5xl mx-auto h-full flex flex-col">
          {/* Header */}

          <h1 className="mt-6 text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-200">
            {isEdit ? "Edit Product" : "Add New Product"}
          </h1>

          <div className="mt-8 flex-1 overflow-y-auto scrollbar-hide">
            <div className="  rounded-xl shadow-sm p-8 border-2 bg-[#252525B2] border-gray-700 sm:p-6 lg:p-8 space-y-3">
              {/* Product Name */}
              <div>
                <label className="text-gray-200 font-semibold text-sm">
                  Product Name <span className="text-red-500">*</span>
                </label>
                <input
                  value={form.productName}
                  onChange={(e) => handleChange("productName", e.target.value)}
                  placeholder="Enter product name"
                  className="w-full mt-2 px-4 py-3 rounded-lg bg-[#252525B2] border border-gray-700 text-sm outline-none "
                />
                {errors.productName && (
                  <p className="text-red-400 text-xs mt-1">
                    {errors.productName}
                  </p>
                )}
              </div>

              {/* Category & Brand */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div ref={categoryRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Product Category <span className="text-red-500">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setCategoryOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left  bg-[#252525B2] border border-gray-700  flex items-center justify-between"
                    >
                      <span
                        className={
                          form.category ? "text-gray-300" : "text-gray-500"
                        }
                      >
                        {form.category
                          ? categories.find(
                              (c) => String(c.id) === String(form.category),
                            )?.name || "Loading..."
                          : "Choose Category"}
                      </span>
                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${categoryOpen ? "rotate-180" : ""}`}
                      />
                    </button>

                    {/* Dropdown */}
                    {categoryOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-black border border-gray-700 text-sm shadow-xl max-h-64 overflow-y-auto flex flex-col scrollbar-hide">
                        {categories.map((cat) => (
                          <div
                            key={cat.id}
                            onClick={() => {
                              handleChange("category", cat.id);
                              setCategoryOpen(false);
                            }}
                            className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${
                              form.category === cat.id
                                ? "bg-white/10 text-gray-400 font-medium"
                                : "hover:bg-white/10"
                            }`}
                          >
                            {cat.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {errors.category && (
                    <p className="text-red-400 text-xs mt-1">
                      {errors.category}
                    </p>
                  )}
                </div>

                <div ref={brandRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Product Brand <span className="text-red-500">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setBrandOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left bg-[#252525B2] border border-gray-700 flex items-center justify-between"
                    >
                      {form.brand.length === 0 ? (
                        <span className="text-gray-500">Select Brands</span>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {/* Use a filter that is case-insensitive to types */}
                          {brands
                            .filter((b) => form.brand.includes(String(b.id)))
                            .map((item) => (
                              <span
                                key={item.id}
                                className="px-2 py-1 text-xs rounded-full bg-[#252525B2] border border-gray-700 text-white"
                              >
                                {item.name}
                              </span>
                            ))}
                        </div>
                      )}
                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${brandOpen ? "rotate-180" : ""}`}
                      />
                    </button>

                    {/* Dropdown */}
                    {brandOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-black border border-gray-700 text-sm shadow-xl max-h-64 overflow-hidden flex flex-col">
                        {/* Search */}
                        <div className="p-2 bg-white/20">
                          <input
                            type="text"
                            placeholder="Search brand..."
                            value={brandSearchTerm}
                            onChange={(e) => setBrandSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg text-sm bg-black border border-gray-700 placeholder-white/40 outline-none"
                          />
                        </div>
                        <div className="overflow-y-auto bg-black scrollbar-hide">
                          {brands
                            .filter((b) =>
                              b.name
                                .toLowerCase()
                                .includes(brandSearchTerm.toLowerCase()),
                            )
                            .map((b) => {
                              const isSelected = form.brand.includes(
                                String(b.id),
                              );

                              return (
                                <div
                                  key={b.id}
                                  onClick={() =>
                                    handleChange(
                                      "brand",
                                      isSelected
                                        ? form.brand.filter((id) => id !== b.id)
                                        : [...form.brand, b.id],
                                    )
                                  }
                                  className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${
                                    isSelected
                                      ? "bg-gray-800 text-gray-400 font-medium"
                                      : "hover:bg-gray-800"
                                  }`}
                                >
                                  {b.name}
                                  {isSelected && (
                                    <span className="text-pink-600 font-bold">
                                      ✓
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}
                  </div>

                  {errors.brand && (
                    <p className="text-red-400 text-xs mt-1">{errors.brand}</p>
                  )}
                </div>
              </div>

              {/* Sub Type & Pattern */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Sub Type */}
                <div ref={subTypeRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Sub Type 
                    {/* <span className="text-red-500">*</span> */}
                  </label>

                  <div className="relative">
                    <button
                      type="button"
                      onClick={() => setSubTypeOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left bg-[#252525B2] border border-gray-700  flex items-center justify-between"
                    >
                      <span
                        className={
                          form.subType ? "text-gray-300" : "text-gray-500"
                        }
                      >
                        {form.subType
                          ? subTypes.find(
                              (s) => String(s.id) === String(form.subType),
                            )?.name || "Loading..."
                          : "Choose Sub Type"}
                      </span>
                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${
                          subTypeOpen ? "rotate-180" : ""
                        }`}
                      />
                    </button>

                    {subTypeOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-black border border-gray-700 text-sm shadow-xl max-h-64 overflow-y-auto">
                        {subTypes.map((s) => (
                          <div
                            key={s.id}
                            onClick={() => {
                              handleChange("subType", s.id);
                              setSubTypeOpen(false);
                            }}
                            className={`px-4 py-3 cursor-pointer text-sm ${
                              form.subType === s.id
                                ? "bg-gray-800 text-gray-400 font-medium"
                                : "hover:bg-gray-800"
                            }`}
                          >
                            {s.name}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {errors.subType && (
                    <p className="text-red-400 text-xs mt-1">
                      {errors.subType}
                    </p>
                  )}
                </div>

                {/* Pattern */}
                <div ref={patternRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Pattern 
                    {/* <span className="text-red-500">*</span> */}
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setPatternOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left bg-[#252525B2] border border-gray-700 flex items-center justify-between"
                    >
                      <span
                        className={
                          form.pattern ? "text-gray-300" : "text-gray-500"
                        }
                      >
                        {form.pattern
                          ? patterns.find(
                              (p) => String(p.id) === String(form.pattern),
                            )?.name || "Loading..."
                          : "Choose Pattern"}
                      </span>

                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${
                          patternOpen ? "rotate-180" : ""
                        }`}
                      />
                    </button>

                    {/* Dropdown */}
                    {patternOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-[#252525B2] border border-gray-700 text-sm shadow-xl max-h-64 overflow-hidden">
                        {/* Search */}
                        {/* <div className="p-2 bg-gray-50">
                          <input
                            type="text"
                            placeholder="Search pattern..."
                            value={patternSearchTerm}
                            onChange={(e) =>
                              setPatternSearchTerm(e.target.value)
                            }
                            className="w-full px-3 py-2 rounded-lg text-sm bg-pink-100 text-pink-900 placeholder-pink-400 outline-none"
                          />
                        </div> */}

                        <div className="overflow-y-auto bg-black scrollbar-hide">
                          {patterns
                            .map((p) => {
                              const isSelected =
                                String(form.pattern) === String(p.id);

                              return (
                                <div
                                  key={p.id}
                                  onClick={() => {
                                    handleChange("pattern", p.id);
                                    setPatternOpen(false);
                                  }}
                                  className={`px-4 py-3 cursor-pointer flex justify-between text-sm ${
                                    isSelected
                                      ? "bg-gray-800 text-gray-400 font-medium"
                                      : "hover:bg-gray-800"
                                  }`}
                                >
                                  {p.name}
                                  {isSelected && (
                                    <span className="font-bold">✓</span>
                                  )}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}
                  </div>

                  {errors.pattern && (
                    <p className="text-red-400 text-xs mt-1">
                      {errors.pattern}
                    </p>
                  )}
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="text-gray-200 font-semibold text-sm">
                  Product Description{" "}
                  <span className="text-gray-400 text-xs">
                    (Max 500 characters)
                  </span>
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => handleChange("description", e.target.value)}
                  rows={3}
                  placeholder="Enter product description"
                  className="w-full mt-2 px-4 py-3 rounded-lg  bg-[#252525B2] border border-gray-700 text-sm outline-none focus:ring-2 focus:ring-white/10"
                />
                {errors.description && (
                  <p className="text-red-400 text-xs mt-1">
                    {errors.description}
                  </p>
                )}
              </div>

              {/* Price & MRP */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-200 font-semibold text-sm">
                    Product Price <span className="text-red-500">*</span>
                  </label>
                  <input
                    value={form.price}
                    onChange={(e) => handleChange("price", e.target.value)}
                    type="number"
                    placeholder="Enter selling price"
                    className="w-full mt-2 px-4 py-3 rounded-lg  bg-[#252525B2] border border-gray-700 text-sm outline-none focus:ring-2 focus:ring-white/10"
                  />
                  {errors.price && (
                    <p className="text-red-400 text-xs mt-1">{errors.price}</p>
                  )}
                </div>

                <div>
                  <label className="text-gray-200 font-semibold text-sm">
                    Product MRP <span className="text-red-500">*</span>
                  </label>
                  <input
                    value={form.mrp}
                    onChange={(e) => handleChange("mrp", e.target.value)}
                    type="number"
                    placeholder="Enter MRP"
                    className="w-full mt-2 px-4 py-3 rounded-lg  bg-[#252525B2] border border-gray-700 text-sm outline-none focus:ring-2 focus:ring-white/10"
                  />
                  {errors.mrp && (
                    <p className="text-red-400 text-xs mt-1">{errors.mrp}</p>
                  )}
                </div>
              </div>

              {/* Colour */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div ref={colourRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Product Colour <span className="text-red-500">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setColourOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left  bg-[#252525B2] border border-gray-700 flex items-center justify-between"
                    >
                      {form.colour.length === 0 ? (
                        <span className="text-gray-500">Select Colour</span>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {/* Use a filter that is case-insensitive to types */}
                          {colours
                            .filter((c) => form.colour.includes(String(c.id)))
                            .map((item) => (
                              <span
                                key={item.id}
                                className="px-2 py-1 text-xs rounded-full bg-white/10 text-white"
                              >
                                {item.name}
                              </span>
                            ))}
                        </div>
                      )}
                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${colourOpen ? "rotate-180" : ""}`}
                      />
                    </button>

                    {/* Dropdown */}
                    {colourOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl  bg-[#252525B2] border border-gray-700 text-sm shadow-xl max-h-64 overflow-hidden flex flex-col">
                        {/* Search */}
                        <div className="p-2 bg-gray-800">
                          <input
                            type="text"
                            placeholder="Search..."
                            value={colourSearchTerm}
                            onChange={(e) =>
                              setColourSearchTerm(e.target.value)
                            }
                            className="w-full px-3 py-2 rounded-lg text-sm bg-[#252525B2] border border-gray-700 placeholder-gray-500 outline-none"
                          />
                        </div>
                        <div className="overflow-y-auto bg-black scrollbar-hide">
                          {colours
                            .filter((c) =>
                              c.name
                                .toLowerCase()
                                .includes(colourSearchTerm.toLowerCase()),
                            )
                            .map((c) => {
                              const isSelected = form.colour.includes(
                                String(c.id),
                              );

                              return (
                                <div
                                  key={c.id}
                                  onClick={() =>
                                    handleChange(
                                      "colour",
                                      isSelected
                                        ? form.colour.filter(
                                            (id) => id !== c.id,
                                          )
                                        : [...form.colour, c.id],
                                    )
                                  }
                                  className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${
                                    isSelected
                                      ? "bg-gray-800 text-gray-400 font-medium"
                                      : "hover:bg-gray-800"
                                  }`}
                                >
                                  {c.name}
                                  {isSelected && (
                                    <span className="text-pink-600 font-bold">
                                      ✓
                                    </span>
                                  )}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}
                  </div>

                  {errors.colour && (
                    <p className="text-red-400 text-xs mt-1">{errors.colour}</p>
                  )}
                </div>

                {/* RIGHT COLUMN — gender */}
                <div ref={genderRef} className="space-y-2">
                  <label className="text-gray-200 font-semibold text-sm">
                    Gender <span className="text-red-500">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setGenderOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left bg-[#252525B2] border border-gray-700 flex items-center justify-between"
                    >
                      <span
                        className={
                          form.gender ? "text-gray-300" : "text-gray-500"
                        }
                      >
                        {form.gender || "Choose gender"}
                      </span>
                      <ChevronDownIcon
                        className={`h-5 w-5 transition-transform ${genderOpen ? "rotate-180" : ""}`}
                      />
                    </button>

                    {/* Dropdown */}
                    {genderOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl  bg-black border border-gray-700 text-sm shadow-xl max-h-64 overflow-hidden flex flex-col">
                        {["Male", "Female"].map((opt) => (
                          <div
                            key={opt}
                            onClick={() => {
                              handleChange("gender", opt); // <-- update form
                              setGenderOpen(false);
                            }}
                            className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${
                              form.gender === opt
                                ? "bg-gray-800 text-gray-400 font-medium"
                                : "hover:bg-gray-800"
                            }`}
                          >
                            {opt}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {errors.gender && (
                    <p className="text-red-400 text-xs mt-1">{errors.gender}</p>
                  )}
                </div>
              </div>

              {/* Images */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* LEFT COLUMN — IMAGE */}
                <div>
                  <label className="text-gray-200 font-semibold text-sm">
                    Product Image <span className="text-red-500">*</span>
                    <span className="text-red-500 text-xs ml-2">
                      Please upload image
                    </span>
                  </label>

                  <div className="flex justify-start">
                    <div className="w-full max-w-xs mt-4 space-y-2">
                      {images.map((img) => (
                        <div
                          key={img.id}
                          className="relative border-2 border-gray-300 rounded-xl overflow-hidden aspect-square bg-gray-50 cursor-pointer"
                          onClick={() => setPreviewImage(img.preview)} // <-- open fullscreen
                        >
                          <img
                            src={img.preview}
                            alt="Preview"
                            className="w-full h-full object-cover"
                          />

                          <button
                            onClick={(e) => {
                              e.stopPropagation(); // prevent triggering fullscreen
                              removeImage(img.id);
                            }}
                            className="absolute top-2 right-2 bg-white rounded-full p-1 shadow"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}

                      {images.length === 0 && (
                        <label
                          onDragOver={(e) => {
                            e.preventDefault();
                            setIsDragging(true);
                          }}
                          onDragLeave={() => setIsDragging(false)}
                          onDrop={handleDrop}
                          className={`border-dashed border-2 rounded-xl aspect-square flex flex-col items-center justify-center text-xs cursor-pointer transition
                          ${
                            isDragging
                              ? "border-purple-500 bg-purple-50 text-purple-600"
                              : "border-gray-300 text-gray-500 hover:border-purple-500"
                          }`}
                        >
                          <UploadCloud size={24} className="mb-2" />
                          {isDragging
                            ? "Drop image here"
                            : "Click or drag image"}
                          <input
                            type="file"
                            accept="image/*"
                            hidden
                            onChange={handleImageUpload}
                          />
                        </label>
                      )}
                    </div>

                    {/* FULLSCREEN PREVIEW */}
                    {previewImage && (
                      <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-fadeIn"
                        onClick={() => setPreviewImage(null)}
                      >
                        {/* Image container */}
                        <div
                          className="relative max-w-4xl w-full mx-4 animate-scaleIn"
                          onClick={(e) => e.stopPropagation()} // prevent close on image click
                        >
                          <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl p-4">
                            <img
                              src={previewImage}
                              alt="Preview"
                              className="w-full max-h-[80vh] object-contain rounded-xl"
                            />
                          </div>

                          {/* Close button */}
                          <button
                            onClick={() => setPreviewImage(null)}
                            className="absolute -top-4 -right-4 bg-white text-gray-900 rounded-full p-2 shadow-lg hover:scale-110 transition"
                          >
                            <X size={20} />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="px-8 py-2 rounded-xl bg-[linear-gradient(90deg,rgba(41,32,195,0.9)_8.65%,rgba(79,70,229,0.9)_37.98%,rgba(37,99,235,0.9)_100%)]
                    bg-white/10 backdrop-blur font-semibold"
                >
                  {loading
                    ? "Saving..."
                    : isEdit
                      ? "Update Product"
                      : "Add Product"}
                </button>

                <button
                  onClick={handleClear}
                  className="px-8 py-2 font-semibold rounded-lg border border-gray-300 text-gray-200"
                >
                  Clear
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
