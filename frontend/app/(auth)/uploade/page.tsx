"use client";

import { useState, useRef, useEffect } from "react";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";
import { UploadCloud, Scan, Heart,MapPin,BarChart3   } from "lucide-react";
import { ProductCardSkeleton, Loader } from "@/app/components/loader";
import SafeImage from "@/app/components/SafeImage";
import Script from "next/script";
import { useRouter } from "next/navigation";

/* ================= TYPES ================= */

interface HistoryItem {
  history_id: string;
  title: string;
  image_url: string | null;
  created_at: string;
}

interface DetectedProduct {
  product_id: string;
  product_title: string;
  category: { id: string; name: string };
  brand: { id: string; name: string };
  price: number;
  mrp: number;
  colour: { id: number; name: string };
  images: { id: string; url: string; is_primary: boolean }[];
  confidence: number;
  itemKey: string; // 🔑 IMPORTANT
}


const extractDotsFromApiResponse = (apiResponse: any) => {
  const persons = apiResponse?.Success?.data || [];

  const dots: {
    id: string;
    x: number;
    y: number;
    label: string;
    itemKey: string;
  }[] = [];

  persons.forEach((person: any, personIndex: number) => {
    const { original_dimensions } = person;
    if (!original_dimensions) return;

    const { width, height } = original_dimensions;

    person.items?.forEach((item: any, itemIndex: number) => {
      if (!item.bbox) return;

      const { x1, y1, x2, y2 } = item.bbox;

      dots.push({
        id: `${personIndex}-${itemIndex}`,
        itemKey: `${personIndex}-${itemIndex}`,
        x: (x1 + x2) / 2 / width,
        y: (y1 + y2) / 2 / height,
        label: item.type,
      });
    });
  });

  return dots;
};



interface Store {
  name: string;
  lat: number;
  lng: number;
  distance_km: number; // km
  address: string;
}

const STORE_CACHE_PREFIX = "store_list_cache";

const getStoreCacheKey = (
  productIds: number[],
  type: "OFFLINE" | "ONLINE"
) => {
  const sortedIds = [...productIds].sort((a, b) => a - b).join(",");
  return `${STORE_CACHE_PREFIX}:${type}:${sortedIds}`;
};

const getCachedStores = (key: string): Store[] | null => {
  try {
    const cached = localStorage.getItem(key);
    if (!cached) return null;
    return JSON.parse(cached);
  } catch {
    return null;
  }
};

const setCachedStores = (key: string, stores: Store[]) => {
  try {
    localStorage.setItem(key, JSON.stringify(stores));
  } catch {
    // silently fail (quota / private mode)
  }
};

const clearStoreListCache = () => {
  if (typeof window === "undefined") return;

  Object.keys(localStorage).forEach((key) => {
    if (key.startsWith(STORE_CACHE_PREFIX)) {
      localStorage.removeItem(key);
    }
  });

  console.log("🧹 Store list cache cleared");
};


/* ================= DUMMY DATA ================= */

const DUMMY_LOCATION = { lat: 19.0760, lng: 72.8777 };

// const DUMMY_PRODUCTS: DetectedProduct[] = [
//   {
//     product_id: "PRD-001",
//     product_title: "Men Slim Fit Denim Jeans",
//     category: { id: "1", name: "Jeans" },
//     brand: { id: "1", name: "Levi's" },
//     price: 2499,
//     mrp: 3499,
//     colour: { id: 1, name: "Blue" },
//     images: [{ id: "1", url: "https://via.placeholder.com/300", is_primary: true }],
//     coordinates: { x: 0.5, y: 0.6, width: 0.3, height: 0.4 },
//     confidence: 0.94,
//   },
// ];

/* ================= COMPONENT ================= */

export default function UploadPage() {
  const [image, setImage] = useState<string | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(false);

  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [detectedProducts, setDetectedProducts] = useState<DetectedProduct[]>([]);
  const [favourites, setFavourites] = useState<string[]>([]);

  const [mapSDKReady, setMapSDKReady] = useState(false);
  const [shouldInitMap, setShouldInitMap] = useState(false);

  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);


  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

const [noProductForDot, setNoProductForDot] = useState(false);

  const [storeType, setStoreType] = useState<"OFFLINE" | "ONLINE">("OFFLINE");
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);
  const [loadingStores, setLoadingStores] = useState(false);

  const [activeItemKey, setActiveItemKey] = useState<string | null>(null);
  const router = useRouter();

  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);


    // which product index is active for each item (dot)
const [activeProductIndexMap, setActiveProductIndexMap] = useState<
  Record<string, number>
>({});


const visibleProducts = (() => {
  const grouped: Record<string, DetectedProduct[]> = {};

  // Group products by itemKey
  detectedProducts.forEach((p) => {
    if (!grouped[p.itemKey]) grouped[p.itemKey] = [];
    grouped[p.itemKey].push(p);
  });

  // 🟢 NO DOT SELECTED
  // → show FIRST product of EACH item
  if (!activeItemKey) {
    return Object.values(grouped).map((products) => products[0]);
  }

  // 🔵 DOT SELECTED
  // → show ALL products of THAT item
  return grouped[activeItemKey] || [];
})();

  const [detectedDots, setDetectedDots] = useState<
    {
      id: string;
      x: number;
      y: number;
      label: string;
      itemKey: string;
    }[]
  >([]);

  const fetchWithTimeout = async (url: string, options: RequestInit, timeout = 8000) => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeout);

    try {
      const res = await fetch(url, {
        ...options,
        signal: controller.signal,
      });
      return res;
    } finally {
      clearTimeout(id);
    }
  };


  const extractHistoryTitle = (record: any): string => {
    const firstResult = record?.search_result?.[0];
    const firstItem = firstResult?.items?.[0];

    if (firstItem?.type) {
      // e.g. "polo shirt" → "Polo Shirt"
      return firstItem.type
        .split(" ")
        .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(" ");
    }

    if (firstItem?.category) {
      return firstItem.category.charAt(0).toUpperCase() + firstItem.category.slice(1);
    }

    return "Outfit";
  };


  const fetchHistoryList = async () => {
    try {
      setHistoryLoading(true);

      const res = await fetchWithTimeout("/api/history", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search: "",
          filter: "",
          startDate: "",
          endDate: "",
          limit: 3,
          offset: 0,
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      let json: any = null;
      try {
        json = await res.json();
      } catch {
        throw new Error("Invalid JSON response from history API");
      }

      const mappedHistory: HistoryItem[] =
        (json?.data || []).map((item: any, index: number) => ({
          history_id: String(item.id ?? index + 1),
          title: extractHistoryTitle(item),
          image_url: item.imagePath || null,
          created_at: new Date(
            item.createdAt || item.created_at
          ).toLocaleString(),
        }));

      setHistoryData(mappedHistory);
    } catch (error) {
      console.error("❌ History API failed:", error);
      setHistoryData([]); // graceful fallback
    } finally {
      setHistoryLoading(false);
      setPageLoading(false);
    }
  };

  /* ================= HISTORY ================= */
  useEffect(() => {
    fetchHistoryList();
  }, []);



  useEffect(() => {
    if (!mapSDKReady || !userLocation || !shouldInitMap) return;
    if (mapRef.current) return;

    const el = document.getElementById("google-map");
    if (!el) return;

    mapRef.current = new google.maps.Map(el, {
      center: userLocation,
      zoom: 14,
    });

    new google.maps.Marker({
      position: userLocation,
      map: mapRef.current,
      icon: {
        url: "http://maps.google.com/mapfiles/ms/icons/blue-dot.png",
      },
    });
  }, [mapSDKReady, userLocation, shouldInitMap]);



useEffect(() => {
  if (!mapRef.current || stores.length === 0) return;

  // Clear old markers
  markersRef.current.forEach(m => m.setMap(null));
  markersRef.current = [];

  const bounds = new google.maps.LatLngBounds();
  let hasValidPoint = false;

  stores.forEach(store => {
    const lat = Number(store.lat);
    const lng = Number(store.lng);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
      console.warn("Invalid store location skipped:", store);
      return;
    }

    const marker = new google.maps.Marker({
      position: { lat, lng },
      map: mapRef.current!,
      title: `${store.name}\n${store.address}`,
    });

    const info = new google.maps.InfoWindow({
      content: `
        <div style="max-width:220px;font-family:Arial;">
          <div style="font-weight:600;font-size:14px;">
            ${store.name}
          </div>
          <div style="font-size:12px;color:#555;">
            ${store.address}
          </div>
          <div style="font-size:12px;color:#777;margin-top:6px;">
            ${store.distance_km} km away
          </div>
        </div>
      `,
    });

    marker.addListener("click", () => {
      infoWindowRef.current?.close();
      info.open(mapRef.current!, marker);
      infoWindowRef.current = info;
    });

    markersRef.current.push(marker);
    bounds.extend(marker.getPosition()!);
    hasValidPoint = true;
  });

  // ✅ Validate userLocation
  if (
    userLocation &&
    Number.isFinite(userLocation.lat) &&
    Number.isFinite(userLocation.lng)
  ) {
    bounds.extend(userLocation);
    hasValidPoint = true;
  }

  // ✅ Only fit bounds if at least one valid coordinate exists
  if (hasValidPoint) {
    mapRef.current.fitBounds(bounds, 60);
  }
}, [stores, userLocation]);


  useEffect(() => {
    if (!navigator.geolocation) {
      setUserLocation(DUMMY_LOCATION);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setUserLocation({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
        });
      },
      () => {
        // fallback if permission denied
        setUserLocation(DUMMY_LOCATION);
      }
    );
  }, []);

  /* ================= IMAGE UPLOAD ================= */

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setDetectedDots([]);
    setDetectedProducts([]);
    setActiveItemKey(null);
    setSelectedFile(file); // ✅ just store file
    setImage(URL.createObjectURL(file)); // ✅ preview only
    clearStoreListCache();
  };

  const scanOutfit = async () => {
    if (!selectedFile) {
      throw new Error("No file selected");
    }

    const formData = new FormData();
    formData.append("file", selectedFile); // 🔥 ACTUAL FILE

    const res = await fetch("/api/search", {
      method: "POST",
      body: formData, // ❗ multipart only
    });

    console.log("🟡 Scan status:", res.status);

    const text = await res.text();
    console.log("🟡 RAW SCAN RESPONSE:", text);

    if (!text) {
      return { success: true };
    }

    try {
      return JSON.parse(text);
    } catch {
      throw new Error("Scan response is not valid JSON");
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();
};

const handleDrop = (e: React.DragEvent) => {
  e.preventDefault();
  e.stopPropagation();

  const file = e.dataTransfer.files?.[0];
  if (!file) return;

  setDetectedDots([]);
  setDetectedProducts([]);
  setActiveItemKey(null);

  setSelectedFile(file);
  setImage(URL.createObjectURL(file));
  clearStoreListCache();
};

  /* ================= SCAN ================= */
 const handleScanOutfit = async () => {
  if (!selectedFile) return;

  setActiveItemKey(null);
  setDetectedProducts([]);
  setDetectedDots([]);
  setActiveProductIndexMap({}); // ✅ RESET
  setLoadingProducts(true);

  try {
    const data = await scanOutfit();

    const products = extractProductsFromApiResponse(data);
    setDetectedProducts(products);

    const dots = extractDotsFromApiResponse(data);
    setDetectedDots(dots);

    // ✅ DEFAULT: FIRST PRODUCT PER ITEM
    const indexMap: Record<string, number> = {};
    products.forEach(p => {
      if (indexMap[p.itemKey] === undefined) {
        indexMap[p.itemKey] = 0;
      }
    });
    setActiveProductIndexMap(indexMap);

    const productIds = products.map(p => Number(p.product_id));
    setSelectedProductIds(productIds);
    fetchStoresFromStoreList(productIds, storeType);
    setShouldInitMap(true);
  } catch (err) {
    console.error("❌ Scan failed:", err);
  } finally {
    setLoadingProducts(false);
  }
};

  const extractProductsFromApiResponse = (apiResponse: any): DetectedProduct[] => {
    const persons = apiResponse?.Success?.data || []; // ✅ FIXED PATH
    const products: DetectedProduct[] = [];

    persons.forEach((person: any, objIndex: number) => {
      const items = person.items || []; // ✅ FIXED

      items.forEach((item: any, itemIndex: number) => {
        const productList = item.product_list || [];
        const itemKey = `${objIndex}-${itemIndex}`;

        productList.forEach((product: any) => {
          products.push({
            product_id: String(product.id),
            product_title: product.name,
            category: {
              id: String(product.category?.id ?? ""),
              name: product.category?.name ?? "",
            },
            brand: {
              id: "",
              name: product.brands?.[0] ?? "",
            },
            price: product.price,
            mrp: product.mrp,
            colour: {
              id: 0,
              name: product.colors?.[0] ?? "",
            },
            images: (product.images || []).map((img: any, index: number) => ({
              id: String(img.id),
              url: img.path,
              is_primary: index === 0,
            })),
            confidence: product.score ?? 0,
            itemKey, // 🔗 links dots ↔ cards
          });
        });
      });
    });

    return products;
  };

const handleSelectItem = (itemKey: string) => {
  setActiveItemKey(itemKey);

  const matchedProducts = detectedProducts.filter(
    (p) => p.itemKey === itemKey
  );

  // 🔴 NO PRODUCTS FOR THIS DOT
  if (matchedProducts.length === 0) {
    setNoProductForDot(true);
    setSelectedProductIds([]);
    setStores([]);          // clear store list
    return;
  }

  // 🟢 PRODUCTS FOUND
  setNoProductForDot(false);

  const productIds = matchedProducts.map((p) => Number(p.product_id));
  setSelectedProductIds(productIds);
  fetchStoresFromStoreList(productIds, storeType);
};




const handleProductClick = (productId: string) => {
  const id = Number(productId);
  if (!id) return;

  setSelectedProductIds([id]);
  fetchStoresFromStoreList([id], storeType);
};



  /* ================= FETCH NEARBY STORES ================= */

const fetchStoresFromStoreList = async (
  productIds: number[],
  type: "OFFLINE" | "ONLINE"
) => {
  if (!userLocation || productIds.length === 0) return;

  const cacheKey = getStoreCacheKey(productIds, type);

  // ✅ 1. CHECK CACHE FIRST
  const cachedStores = getCachedStores(cacheKey);
  if (cachedStores) {
    console.log("🟣 Using cached stores:", cacheKey);
    setStores(cachedStores);
    return;
  }

  console.log("🟢 Fetching stores from API:", productIds, type);

  setLoadingStores(true);
  setStores([]);

  try {
    const res = await fetch("/api/store-list", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        products_id: productIds,
        store_type: type,
        latitude: userLocation.lat,
        longitude: userLocation.lng,
      }),
    });

    const json = await res.json();

    const mappedStores: Store[] = (json.data || []).map((s: any) => ({
      name: s.store_name,
      lat: Number(s.latitude),
      lng: Number(s.longitude),
      distance_km: Number(s.distance_km ?? 0),
      address: s.address || "-",
    }));

    // ✅ 2. SAVE TO CACHE
    setCachedStores(cacheKey, mappedStores);

    setStores(mappedStores);
  } catch (err) {
    console.error("❌ Store list failed", err);
    setStores([]);
  } finally {
    setLoadingStores(false);
  }
};



  return (
    <DashboardLayout>

      <Script
        src={`https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=marker`}
        strategy="afterInteractive"
        onLoad={() => setMapSDKReady(true)}
      />

      {pageLoading && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
          <Loader size="lg" />
        </div>
      )}

      <div className="w-full bg-[#1C1B1B] rounded-2xl p-4 sm:p-6 max-h-full overflow-y-auto scrollbar-hide">

        {/* MAIN GRID */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

          {/* LEFT COLUMN */}
          <div className="lg:col-span-4 flex flex-col mx-4 xl:mx-10 gap-6">

            {/* Upload Section */}
            <span className="text-2xl text-gray-200 font-medium tracking-wide">
              Active Recognition
            </span>
            <div className="rounded-4xl px-4 lg:px-6 xl:px-10 pt-6 lg:pt-8 pb-4 flex flex-col gap-4  border border-white/10">
              <label
                htmlFor={image ? undefined : "upload"}
                 onDragOver={handleDragOver}
                onDrop={handleDrop}
                className={`aspect-6/7 rounded-4xl flex flex-col items-center justify-center overflow-visible text-center cursor-pointer transition-all duration-300
                  ${image ? "border-none" : "border-2 border-dashed border-gray-500 hover:bg-gray-800"}
                `}
              >
                {image ? (
                  <div className="relative w-full h-full flex items-center justify-center ">
                    <img
                      src={image}
                      alt="Uploaded"
                      className="relative max-h-full max-w-full object-cover rounded-lg z-10"
                    />

                    {/* DOTS */}
                    {detectedDots.map((dot) => (
                      <span
                        key={dot.id}
                        onClick={() => handleSelectItem(dot.itemKey)}
                        className="absolute cursor-pointer group z-20"
                        style={{
                          left: `${dot.x * 100}%`,
                          top: `${dot.y * 100}%`,
                          transform: "translate(-50%, -50%)",
                        }}
                      >

                        {/* 🏷️ HOVER TITLE */}
                        <div className="absolute left-1/2 top-[-30px]
                                        -translate-x-1/2 bg-white
                                        text-gray-800 text-xs
                                        z-50
                                        px-3 py-2 rounded-xl border shadow-lg
                                        opacity-0 scale-95 translate-y-1
                                        transition-all duration-200 ease-out
                                        group-hover:opacity-100
                                        group-hover:scale-100
                                        group-hover:translate-y-0
                                        pointer-events-none
                                        text-center
                                        min-w-[120px] 
                                      "
                        >
                          {dot.label}
                        </div>

                        {/* OUTER RING (UNCHANGED) */}
                        <span
                          className="
                            w-4 h-4
                            rounded-full
                            border-2 border-white
                            bg-white/30
                            shadow-md
                            flex items-center justify-center
                          "
                        >
                          {/* INNER DOT */}
                          <span
                            className="
                          w-2 h-2
                          rounded-full
                          bg-white
                        "
                          />
                        </span>
                      </span>
                    ))}

                  </div>
                ) : (
                  <>
                    <UploadCloud className="text-gray-500 mb-2" />
                    <p className="text-sm font-medium text-gray-700">
                      Click or drag image to upload
                    </p>
                    <p className="text-xs text-gray-400 mt-1">
                      JPG, PNG, WEBP supported
                    </p>
                  </>
                )}
              </label>

              <input
                ref={fileInputRef}
                id="upload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect}
              />

              <button
                disabled={!image}
                onClick={handleScanOutfit}
                className="
                  mt-2 py-3 px-5 rounded-md font-semibold
                  flex items-center justify-center gap-2
                  bg-[linear-gradient(90deg,rgba(210,51,225,0.8)_37.98%,rgba(158,34,185,0.7965)_70.67%,rgba(60,1,111,0.79)_100%)]
                  shadow-[0px_4px_6px_-4px_rgba(236,91,19,0.2),0px_10px_15px_-3px_rgba(236,91,19,0.2)]
                  text-white
                  transition-all duration-200
                  hover:brightness-110
                  active:scale-95
                  disabled:opacity-50
                  disabled:cursor-not-allowed
                "
              >
                <Scan size={16} />
                <span>Scan Outfit</span>
              </button>

              <span
                onClick={() => fileInputRef.current?.click()}
                className="
              text-sm text-center text-gray font-semibold opacity-60
              cursor-pointer transition-colors duration-200
              hover:text-purple-800
            "
              >
                Choose Another photo
              </span>
            </div>


            {/* History */}
            <div className="hidden lg:block">
              <h2 className="text-xl font-semibold mb-3">Recent Scans
              <span
                    onClick={() => router.push("/history")}
                    className="text-sm text-gray-400 cursor-pointer ml-50 hover:text-gray-200 transition-colors ">
                    View All
                  </span>
</h2>
              {historyLoading ? (
                <Loader />
              ) : historyData.length === 0 ? (
                <div className="text-center text-gray-200 py-10 text-sm">
                  No history found.
                </div>
              ) : (
                <div className="flex flex-col gap-3 p-6">
                  {historyData.map((item, index) => (
                    <div
                      key={item.history_id}
                      className="rounded-md  border border-white/10 shadow-md flex items-center px-4 py-2 gap-3
                         hover transition cursor-pointer 
                         transform-gpu transition-all duration-200 ease-out
                         hover:shadow-2xl hover:-translate-y-1"
                    >
                      <div className="w-12 h-12 rounded-md overflow-hidden bg-gray-100">
                        <SafeImage src={item.image_url} alt="History image" />
                      </div>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium text-gray-200">
                          {item.title}
                        </span>
                        <p className="text-xs text-gray-400">
                          {item.created_at}
                        </p>
                      </div>

                    </div>
                  ))}
                  
                </div>
              )}
            </div>


          </div>

          {/* RIGHT COLUMN */}
          <div className="lg:col-span-8 flex flex-col gap-6">

            {/* Recognized Items */}
<div className="relative w-full">

  {/* Header */}
  <div className="flex justify-between items-center">
    
    <h2 className="text-2xl font-semibold">
      <BarChart3 className="inline mb-1 mr-2" /> 
      Recognized Items</h2>
    {detectedProducts.length > 0 &&(
      <button 
          className="w-[200px] mt-1 py-1
bg-[linear-gradient(90deg,rgba(210,51,225,0.8)_37.98%,rgba(158,34,185,0.7965)_70.67%,rgba(60,1,111,0.79)_100%)]
text-white font-bold text-xl
shadow-[0px_4px_6px_-4px_rgba(236,91,19,0.2),0px_10px_15px_-3px_rgba(236,91,19,0.2)]
hover:opacity-90
transition-all duration-200
rounded-lg

"
          onClick={() => {
          setActiveItemKey(null);

            // Save recognized list
            sessionStorage.setItem(
              "recognizedProducts",
              JSON.stringify(visibleProducts)
            );

            router.push("/try-on");
        }}
        >
          Try On
        </button>

     
    )}
  </div>

  {/* Content */}
  {noProductForDot ? (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-lg font-semibold text-gray-600">
        No products found for this item
      </p>
      <p className="text-sm text-gray-400 mt-2">
        Try selecting another or scan a different outfit
      </p>
    </div>
  ) : loadingProducts ? (
    /* Loader grid */
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {Array.from({ length: 3 }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  ) : detectedProducts.length === 0 ? (
    /* Empty state */
    <div className="text-center text-gray-400 py-30 text-xl">
      No products found. Scan an outfit to see results.
    </div>
  ) : (
    /* Horizontal scroll */
    <div
      id="recognized-scroll"
      className="
        flex flex-nowrap gap-6
        overflow-x-auto overflow-y-hidden
        scrollbar-hide
        snap-x snap-mandatory
        scroll-smooth
        px-4 py-4
      "
    >
      {visibleProducts.map((product) => {
        const primaryImage =
          product.images.find(img => img.is_primary)?.url ||
          product.images[0]?.url;

        return (
          <div
            key={`${product.product_id}-${product.itemKey}`}
            onClick={() => handleProductClick(product.product_id)}
            className={`
              relative
              min-w-[240px] max-w-[240px]
              flex-shrink-0 snap-start
              origin-bottom
              border border-white/10 rounded-2xl px-4 py-4 shadow-lg
              transition-all duration-200
              cursor-pointer
              hover:ring-2 hover:ring-white/10
              hover:scale-[1.03] hover:shadow-xl
              ${
                activeItemKey === product.itemKey
                  ? "ring-2 ring-gray-500 scale-[1.03] shadow-xl"
                  : ""
              }
            `}
          >
            {/* Product Image */}
            <div className="w-full aspect-square bg-gray-100 rounded-xl mb-2 overflow-hidden">
              <SafeImage src={primaryImage} alt="Product image" />
            </div>

            {/* Title */}
            <p className="text-sm text-gray-200 font-medium leading-tight px-1 truncate">
              {product.product_title}
            </p>

            {/* Brand */}
            <p className="text-xs text-gray-300 leading-tight px-1">
              {product.brand.name}
            </p>

            {/* Price + Confidence */}
            <div className="flex justify-between items-center px-1 mt-1 text-sm">
              <span className="font-semibold">₹ {product.price}</span>
              <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 text-green-700">
                {Math.round(product.confidence * 100)}%
              </span>
            </div>
          </div>
        );
      })}
    </div>
  )}
</div>



            <p className="text-gray-200 font-medium">
              <MapPin  className="inline mb-1 mr-1" />
              Shop from 3 nearby stores or 2 online sellers.
            </p>

            {/* Map + Store List Container */}
            <div className="border border-white/10 p-6 shadow-sm rounded-xl">
              <div className="flex flex-col md:flex-row gap-8">

                {/* LEFT: The Interactive Map */}
                <div className="w-full md:w-1/2 relative h-[400px]">
                  {shouldInitMap ? (
                    <div
                      id="google-map"
                      className="w-full h-full rounded-3xl overflow-hidden border border-gray-100"
                    />
                  ) : (
                    <div className="absolute inset-0 flex items-center justify-center bg-gray-800 rounded-3xl">
                      <p className="text-gray-500 font-medium text-center">
                        Upload and scan an image <br /> to see nearby stores
                      </p>
                    </div>
                  )}
                </div>


                {/* RIGHT: Store List */}
                <div className="w-full md:w-1/2 flex flex-col">
                  {/* Header Tabs */}
                  <div className="flex gap-4 mb-6 border border-white/30 rounded-full p-1 self-start">
                    <button
                      onClick={() => {
                        const type = "OFFLINE";
                        setStoreType(type);
                        fetchStoresFromStoreList(selectedProductIds, type);
                      }}

                      className={`px-6 py-2 rounded-full text-sm font-medium
      ${storeType === "OFFLINE"
                          ? "bg-purple-600 text-white"
                          : "text-gray-400"
                        }`}
                    >
                      Nearby Stores
                    </button>

                    <button
                      onClick={() => {
                        const type = "ONLINE";
                        setStoreType(type);
                        fetchStoresFromStoreList(selectedProductIds, type);
                      }}
                      className={`px-6 py-2 rounded-full text-sm font-medium
      ${storeType === "ONLINE"
                          ? "bg-purple-600 text-white"
                          : "text-gray-400"
                        }`}
                    >
                      Online
                    </button>
                  </div>

                  {/* <div className="flex items-center gap-3 mb-6">
                    <div className="bg-cyan-100 p-2 rounded-lg">
                      <Scan size={20} className="text-cyan-600" />
                    </div>
                    <div>
                      <h3 className="font-bold text-gray-200">Nearby Stores</h3>
                      <p className="text-xs text-gray-400">Visit in person</p>
                    </div>
                  </div> */}

                  <div className="flex flex-col gap-4 overflow-y-auto max-h-[300px] pr-2 scrollbar-hide">
                    {loadingStores ? (
                      <div className="flex justify-center items-center py-10">
                        <Loader size="md" />
                      </div>
                    ) : stores.length > 0 ? (
                      stores.map((store, i) => (
                        <div
                          key={i}
                          className="group border border-white/10 rounded-2xl p-4 flex justify-between items-start hover:border-white/10 hover:bg-white/10 transition-all cursor-pointer"
                        >
                          <div className="flex flex-col gap-1">
                            <p className="font-bold text-gray-300 text-sm">{store.name}</p>
                            <p className="text-[11px] text-gray-400">{store.address}</p>

                          </div>
                          <span className="text-xs font-bold text-gray-400 group-hover:text-blue-100">
                            {store.distance_km} km
                          </span>
                        </div>
                      ))
                    ) : (
                      <div className="text-center py-10 text-gray-400 text-sm italic">
                        Searching for nearby fashion hubs...
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

          </div>


          {/* Histor */}
          <div className="block lg:hidden">
            <h2 className="text-4xl font-semibold mb-3">History</h2>

            {historyLoading ? (
              <Loader />
            ) : historyData.length === 0 ? (
              <div className="text-center text-gray-400 py-10 text-sm">
                No history found.
              </div>
            ) : (
              <div className="flex flex-col gap-3 p-6">
                {historyData.map((item, index) => (
                  <div
                    key={item.history_id}
                    className="bg-white rounded-xl shadow-sm flex items-center px-4 py-2 gap-3
        hover:bg-gray-50 transition cursor-pointer"
                  >
                    <div className="w-12 h-12 rounded-lg overflow-hidden bg-gray-100">
                      <SafeImage src={item.image_url} alt="History image" />
                    </div>

                    <div className="flex flex-col">
                      <span className="text-sm font-medium text-gray-700">
                        Outfit {index + 1}
                      </span>
                      <p className="text-xs text-gray-400">
                        {item.created_at}
                      </p>
                    </div>
                  </div>
                ))}
                <span className="text-sm text-gray-400 cursor-pointer">
                  View All
                </span>
              </div>

            )}

          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}