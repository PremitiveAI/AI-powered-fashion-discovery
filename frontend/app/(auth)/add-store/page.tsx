"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import Toast from "@/app/components/toast"
import { Loader } from "@/app/components/loader";
import { ChevronDownIcon } from "@heroicons/react/24/outline";
import { ArrowLeft } from "lucide-react";

type Errors = {
  [key: string]: string;
};

export default function AddStorePage() {

  const router = useRouter();
  const [form, setForm] = useState({
    storeName: "",
    storeType: "",
    website: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
    phone: "",
    email: "",
    latitude: "",
    longitude: "",
  });


  const searchParams = useSearchParams();
  const id = searchParams.get("id");
  const [userId, setUserId] = useState("");
  const isEdit = Boolean(id);

  const [errors, setErrors] = useState<Errors>({});
  const [isFetchingLocation, setIsFetchingLocation] = useState(false);
  const [loading, setLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const [productOptions, setProductsOptions] = useState<{ value: string; label: string }[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [productOpen, setProductsOpen] = useState(false);
  const [productSearchTerm, setProductsSearchTerm] = useState("");
  const productRef = useRef<HTMLDivElement>(null);
  const [productTypeError, setProductTypeError] = useState("");

  const storeRef = useRef<HTMLDivElement>(null);
  const [storeOpen, setStoreOpen] = useState(false);

  const showToast = (message: string, type: "success" | "error") => {
    setToastMessage(message);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const handleChange = (key: string, value: string) => {
    setForm(prev => ({ ...prev, [key]: value }));
    if (errors[key]) {
      setErrors(prev => ({ ...prev, [key]: "" }));
    }
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (storeRef.current && !storeRef.current.contains(event.target as Node)) {
        setStoreOpen(false);
      }

      if (productRef.current && !productRef.current.contains(event.target as Node)) {
        setProductsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const getLabelsByIds = (ids: string[], options: { value: string; label: string }[]) => {
    return options
      .filter((opt) => ids.includes(opt.value))
      .map((opt) => opt.label);
  };

  const validate = () => {
    const newErrors: Errors = {};

    if (!form.storeName.trim())
      newErrors.storeName = "Store name is required";

    if (!form.address.trim())
      newErrors.address = "Address is required";

    if (!form.city.trim())
      newErrors.city = "City is required";

    if (!form.state.trim())
      newErrors.state = "State is required";

    if (!/^\d{6}$/.test(form.pincode))
      newErrors.pincode = "Enter valid 6 digit pincode";

    if (!/^\d{10}$/.test(form.phone))
      newErrors.phone = "Enter valid 10 digit phone number";

    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email))
      newErrors.email = "Enter valid email address";

    const latValue = String(form.latitude || "").trim();
    if (latValue === "") {
      newErrors.latitude = "Latitude is required";
    } else {
      const lat = Number(latValue);
      if (isNaN(lat) || lat < -90 || lat > 90) {
        newErrors.latitude = "Enter valid latitude (-90 to 90)";
      }
    }

    const lngValue = String(form.longitude || "").trim();
    if (lngValue === "") {
      newErrors.longitude = "Longitude is required";
    } else {
      const lng = Number(lngValue);
      if (isNaN(lng) || lng < -180 || lng > 180) {
        newErrors.longitude = "Enter valid longitude (-180 to 180)";
      }
    }

    if (!form.storeType)
      newErrors.storeType = "Please select store type";

    if (!productTypeError)
      setProductTypeError("Please select product type");

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const getCurrentLocation = () => {
    if (!navigator.geolocation) {
      alert("Geolocation not supported");
      return;
    }

    setIsFetchingLocation(true);

    navigator.geolocation.getCurrentPosition(
      async (position: GeolocationPosition) => {
        const { latitude, longitude } = position.coords;
        const apiKey = 'BetWb7Wc0q0Uj9FihLMtobmuhNYEms8gJlRZFrKb';
        const url = `https://api.olamaps.io/places/v1/reverse-geocode?latlng=${latitude},${longitude}&api_key=${apiKey}`;

        try {
          const res = await fetch(url);
          const data = await res.json();

          if (data.status === 'ok' && data.results && data.results.length > 0) {

            // FIX: Added (r: any) to satisfy TypeScript
            const bestMatch = data.results.find((r: any) =>
              r.types.includes("premise") ||
              r.types.includes("point_of_interest") ||
              r.types.includes("establishment")
            ) || data.results[0];

            // FIX: Explicitly typed 'type' as string
            const getComponent = (type: string): string =>
              bestMatch.address_components?.find((c: any) => c.types.includes(type))?.long_name || "";

            setForm((prev: any) => ({
              ...prev,
              latitude: latitude.toString(),
              longitude: longitude.toString(),
              // Logic to prefer the name of the building if it's separate from the address
              address: bestMatch.name && !bestMatch.formatted_address.includes(bestMatch.name)
                ? `${bestMatch.name}, ${bestMatch.formatted_address}`
                : bestMatch.formatted_address,
              city: getComponent("locality") || getComponent("administrative_area_level_2"),
              state: getComponent("administrative_area_level_1"),
              pincode: getComponent("postal_code"),
            }));

            setErrors((prev: any) => ({
              ...prev,
              address: "", city: "", state: "", pincode: "", latitude: "", longitude: "",
            }));
          } else {
            alert("No address found for this location.");
          }
        } catch (err) {
          console.error("Ola Maps Error:", err);
          alert("Failed to fetch address from Ola Maps");
        } finally {
          setIsFetchingLocation(false);
        }
      },
      (error) => {
  console.error("Geolocation error:", error);
  setIsFetchingLocation(false);

  switch (error.code) {
    case error.PERMISSION_DENIED:
      alert("Please enable location permissions in your browser settings.");
      break;
    case error.POSITION_UNAVAILABLE:
      alert("Location information is unavailable. Check your GPS/network.");
      break;
    case error.TIMEOUT:
      alert("The request to get user location timed out. Try again.");
      break;
    default:
      alert("An unknown error occurred.");
      break;
  }
}
    );
  };

  useEffect(() => {
    async function fetchProductsOptions() {
      try {
        const res = await fetch("/api/product-type", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            search: "", filter: "", startDate: "", endDate: "",
            sort: "createdAt", order: "DESC", limit: 100, offset: 0,
          }),
        });
        const json = await res.json();
        const arr = Array.isArray(json?.data) ? json.data : [];

        setProductsOptions(
          arr.map((item: any) => ({
            value: String(item.id), // Store as string for consistency
            label: item.name,
          }))
        );
      } catch (err) {
        console.error("Failed to fetch product types", err);
      }
    }
    fetchProductsOptions();
  }, []);

  const fetchStoreDetails = async (id: string) => {
    try {
      setLoading(true);
      const res = await fetch(`/api/store-detail/${encodeURIComponent(id)}`);
      const json = await res.json();

      if (!res.ok) throw new Error(json?.message || "Failed to fetch");

      const data = json?.Success?.data;

      if (data) {
        setUserId(data.id);
        setForm({
          storeName: data.store_name || "",
          storeType: data.store_type === "ONLINE" ? "Online" : "Offline",
          website: data.website || "",
          address: data.address || "",
          city: data.city || "",
          state: data.state || "",
          pincode: data.pincode || "",
          phone: data.phone || "",
          email: data.email || "",
          latitude: data.latitude || "",
          longitude: data.longitude || "",
        });

        // ✅ SET DEFAULT SELECTED PRODUCTS FROM API
        // This converts [2, 1] into ["2", "1"] to match your dropdown options
        if (data.products_id && Array.isArray(data.products_id)) {
          setSelectedProducts(data.products_id.map((id: any) => String(id)));
        }
      }
    } catch (error) {
      console.error("❌ FETCH ERROR:", error);
    } finally {
      setLoading(false);
    }
  };

  // 5. Submit Handler
  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      setLoading(true);
      const res = await fetch("/api/add-store", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: isEdit ? Number(userId) : 0,
          store_name: form.storeName,
          address: form.address,
          city: form.city,
          state: form.state,
          pincode: form.pincode,
          latitude: form.latitude,
          longitude: form.longitude,
          phone: form.phone,
          email: form.email,
          store_type: form.storeType === "Online" ? "ONLINE" : "OFFLINE",
          website: form.website,
          products_id: selectedProducts.map((id) => Number(id)),
        }),
      });

      const data = await res.json();
      if (res.ok) {
        const message = data?.Success?.message || "Store added successfully!";
        showToast(message, "success");
        router.push("/store-list");
      }else {
        showToast(data?.Error?.message || "Something went wrong","error");
      }
    } catch (err) {
      showToast("Server error", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      console.log("Employee ID:", id);
      setUserId(id);
      fetchStoreDetails(id);
    } else {
      setUserId("0");
    }
  }, [id]);

  const handleClear = () => {
    setForm({
      storeName: "",
      storeType: "",
      website: "",
      address: "",
      city: "",
      state: "",
      pincode: "",
      phone: "",
      email: "",
      latitude: "",
      longitude: "",
    });
    // setSelectedProducts();
    setErrors({})
  };

  return (
    <DashboardLayout>
      <div className="bg-[#1C1B1B] h-full w-full flex flex-col overflow-y-auto scrollbar-hide px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        {isEdit && (
          <button
            onClick={() => router.back()}
            className="flex items-center gap-2 text-xl sm:text-xl lg:text-2xl
            font-bold text-gray-900 px-2">
            <ArrowLeft className="w-6 h-6 sm:w-6 sm:h-6 lg:w-7 lg:h-7" />
            <span>Back</span>
          </button>
        )}

        {loading && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <Loader size="lg" />
          </div>
        )}

        {toastMessage && <Toast message={toastMessage} type={toastType} />}

        <div className="max-w-5xl w-full mx-auto">
          {/* Header */}

          <h1 className={`text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-300 ${isEdit ? "mt-4" : "mt-0"
            }`}>
            {isEdit ? "Edit Store" : "Add New Store"}
          </h1>

          <div className="mt-8 flex-1 overflow-y-auto scrollbar-hide">
            <div className="bg-[#252525B2] rounded-xl shadow-sm p-8 border border-white/10 sm:p-6 lg:p-8 space-y-3">
              {/* Store Name */}
              <div>
                <label className="text-gray-300 font-semibold text-sm">Store Name</label>
                <span className=" text-red-400 text-xs ml-2">*</span>
                <input
                  name="storeName"
                  placeholder="e.g. Trendy Fashion Hub"
                  value={form.storeName}
                  onChange={(e) => handleChange("storeName", e.target.value)}
                  type="text"
                  className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all
                  truncate sm:whitespace-normal "/>
                {errors.storeName && <p className="text-red-400 text-xs mt-1 ">{errors.storeName}</p>}
              </div>

              {/* Phone / Email */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-300 font-semibold text-sm">Phone Number</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="phone"
                    placeholder="e.g. 18.5204"
                    value={form.phone}
                    onChange={(e) => handleChange("phone", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600  text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.phone && <p className="text-red-400 text-xs mt-1">{errors.phone}</p>}
                </div>

                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">Email</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="email"
                    placeholder="e.g. store.support@example.com"
                    value={form.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.email && <p className="text-red-400 text-xs mt-1">{errors.email}</p>}
                </div>
              </div>

              {/* Address Section */}
              <div className="flex justify-between items-center">
                <label className="text-gray-300 font-semibold text-sm">
                  Address
                  <span className="text-red-400 text-xs ml-1">*</span>
                </label>

                {/* Use Current Location Button */}
                <div className="flex justify-end items-center gap-3">
                  {isFetchingLocation && (
                    <span className="text-sm text-gray-400 animate-pulse">
                      Fetching location…
                    </span>
                  )}
                  <button
                    type="button"
                    onClick={getCurrentLocation}
                    disabled={isFetchingLocation}
                    className="px-4 py-2 text-sm rounded-lg border border-blue-400 text-blue-500 hover:bg-blue-900 disabled:opacity-50"
                  >
                    📍 Use Current Location
                  </button>
                </div>
              </div>

              {/* Full Address */}
              <div className="flex flex-col">
                <textarea
                  name="address"
                  placeholder="Shop No. 12, 2nd Floor, Phoenix Mall, Senapati Bapat Road"
                  value={form.address}
                  onChange={(e) => handleChange("address", e.target.value)}
                  rows={2}
                  className="w-full px-4 py-2 rounded-lg border border-gray-600 text-sm outline-none transition-all resize-none overflow-hidden focus:outline-none focus:ring-2 focus:ring-gray-700"
                  onInput={(e) => {
                    const target = e.currentTarget;
                    target.style.height = "auto";
                    target.style.height = `${target.scrollHeight}px`;
                  }}
                />
                {errors.address && (
                  <p className="text-red-400 text-xs mt-1">{errors.address}</p>
                )}
              </div>

              {/* City / State / Pincode */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">City</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="city"
                    placeholder="e.g. Pune"
                    value={form.city}
                    onChange={(e) => handleChange("city", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.city && <p className="text-red-400 text-xs mt-1">{errors.city}</p>}
                </div>

                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">State</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="state"
                    placeholder="e.g. Maharashtra"
                    value={form.state}
                    onChange={(e) => handleChange("state", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.state && <p className="text-red-400 text-xs mt-1">{errors.state}</p>}
                </div>

                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">Pincode</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="pincode"
                    placeholder="e.g. 411016"
                    value={form.pincode}
                    onChange={(e) => handleChange("pincode", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.pincode && <p className="text-red-400 text-xs mt-1">{errors.pincode}</p>}
                </div>
              </div>

              {/* Latitude / Longitude */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">Latitude</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="latitude"
                    placeholder="e.g. 18.5204"
                    value={form.latitude}
                    onChange={(e) => handleChange("latitude", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.latitude && <p className="text-red-400 text-xs mt-1">{errors.latitude}</p>}
                </div>

                <div>
                  <label className="text-gray-300 font-semibold text-sm capitalize">Longitude</label>
                  <span className="text-red-400 text-xs ml-2">*</span>
                  <input
                    name="longitude"
                    placeholder="e.g. 73.8567"
                    value={form.longitude}
                    onChange={(e) => handleChange("longitude", e.target.value)}
                    type="text"
                    className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all focus:outline-none focus:ring-2 focus:ring-gray-700"
                  />
                  {errors.longitude && <p className="text-red-400 text-xs mt-1">{errors.longitude}</p>}
                </div>
              </div>

              {/* Store Type / Product */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div ref={storeRef} className="space-y-2">
                  <label className="text-gray-300 font-semibold text-sm">
                    Store Type
                    <span className="text-red-400 text-xs ml-2">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setStoreOpen((p) => !p)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left border border-gray-600 flex items-center justify-between">
                      <span className={form.storeType ? "text-gray-800" : "text-gray-400"}>
                        {form.storeType || "Choose Store Type"}
                      </span>
                      <ChevronDownIcon className={`h-5 w-5 transition-transform ${storeOpen ? "rotate-180" : ""}`} />
                    </button>

                    {/* Dropdown */}
                    {storeOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-black border border-gray-600 shadow-xl max-h-64 overflow-hidden flex flex-col">

                        {["Online", "Offline", "Both"].map((opt) => (
                          <div
                            key={opt}
                            onClick={() => {
                              handleChange("storeType", opt); // <-- update form
                              setStoreOpen(false);
                            }}
                            className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${form.storeType === opt ? "bg-pink-50 text-pink-700 font-medium" : "hover:bg-gray-700"
                              }`} >
                            {opt}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  {errors.storeType && (
                    <p className="text-red-400 text-xs mt-1">
                      {errors.storeType}
                    </p>
                  )}
                </div>

                <div ref={productRef} className="space-y-2">
                  <label className="text-gray-300 font-semibold text-sm">
                    Product Type
                    <span className="text-red-400 text-xs ml-2">*</span>
                  </label>

                  <div className="relative">
                    {/* Trigger */}
                    <button
                      type="button"
                      onClick={() => setProductsOpen(!productOpen)}
                      className="w-full mt-1 px-4 py-3 rounded-xl text-sm text-left border border-gray-600 flex items-center justify-between"
                    >
                      {selectedProducts.length === 0 ? (
                        <span className="text-gray-400">Select Product Types</span>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {getLabelsByIds(selectedProducts, productOptions).map((label) => (
                            <span key={label} className="px-2 py-1 text-xs rounded-full bg-pink-400 text-white">
                              {label}
                            </span>
                          ))}
                        </div>
                      )}
                      <ChevronDownIcon className={`h-5 w-5 transition-transform ${productOpen ? "rotate-180" : ""}`} />
                    </button>

                    {productOpen && (
                      <div className="absolute z-50 w-full mt-2 rounded-xl bg-black border border-gray-600 shadow-xl max-h-64 overflow-hidden flex flex-col">
                        <div className="p-2 bg-black">
                          <input
                            type="text"
                            placeholder="Search..."
                            value={productSearchTerm}
                            onChange={(e) => setProductsSearchTerm(e.target.value)}
                            className="w-full px-3 py-2 rounded-lg text-sm bg-gray-800 text-gray-300 placeholder-gray-400 outline-none" />
                        </div>
                        <div className="overflow-y-auto">
                          {productOptions
                            .filter((opt) => opt.label.toLowerCase().includes(productSearchTerm.toLowerCase()))
                            .map((opt) => {
                              const isSelected = selectedProducts.includes(opt.value);
                              return (
                                <div
                                  key={opt.value}
                                  onClick={() => {
                                    setSelectedProducts((prev) => {
                                      const isSelected = prev.includes(opt.value);
                                      const nextProducts = isSelected
                                        ? prev.filter((id) => id !== opt.value)
                                        : [...prev, opt.value];
                                      if (nextProducts.length > 0) {
                                        setProductTypeError("");
                                      }
                                      return nextProducts;
                                    });
                                  }}
                                  className={`px-4 py-3 cursor-pointer flex items-center justify-between text-sm ${isSelected ? "bg-pink-50 text-pink-700 font-medium" : "hover:bg-gray-700"
                                    }`}
                                >
                                  {opt.label}
                                  {isSelected && <span className="text-pink-600 font-bold">✓</span>}
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    )}
                  </div>
                  {productTypeError && (
                    <p className="text-red-400 text-xs mt-1">
                      {productTypeError}
                    </p>
                  )}
                </div>
              </div>

              {/* Website */}
              <div>
                <label className="text-gray-300 font-semibold text-sm">Website</label>
                <span className="text-gray-400 text-xs ml-2">(Optional)</span>
                <input
                  name="website"
                  placeholder="e.g. https://www.trendyfashionhub.com"
                  value={form.website}
                  onChange={(e) => handleChange("website", e.target.value)}
                  type="url"
                  className="w-full mt-2 px-4 py-3 rounded-lg border border-gray-600 text-sm outline-none transition-all
                  truncate sm:whitespace-normal focus:outline-none focus:ring-2 focus:ring-gray-700"/>
              </div>

              {/* Buttons */}
              <div className="flex gap-4 pt-4">
                <button
                  type="submit"
                  onClick={handleSubmit}
                  disabled={loading}
                  className="px-8 py-2 rounded-xl bg-[linear-gradient(90deg,rgba(41,32,195,0.9)_8.65%,rgba(79,70,229,0.9)_37.98%,rgba(37,99,235,0.9)_100%)]
                    text-white font-semibold"
                >
                  {loading
                    ? "Saving..."
                    : isEdit
                      ? "Update Store"
                      : "Add Store"}
                </button>

                <button
                  type="reset"
                  onClick={handleClear}
                  className="px-8 py-2 font-semibold rounded-lg border border-gray-300 text-gray-300">
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
