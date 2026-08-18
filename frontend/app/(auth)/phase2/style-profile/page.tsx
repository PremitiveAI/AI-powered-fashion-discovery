"use client";

import { useRouter } from "next/navigation";
import { useState, useRef, useEffect } from "react";
import { Camera, Info, Mars, Venus, CheckCircle2 } from "lucide-react";
import Toast from "@/app/components/toast";
import { Loader } from "@/app/components/loader";
import { DashboardLayout } from "@/app/(main)/dashboard/DashboardLayout";


interface Categories {
  id: number;
  name: string;
  type: string;
  description: string;
  gallery_id: number;
  image_url: string;
  gender: string;
}

interface Sizes {
  id: number;
  name: string;
  full_name: string;
  gender: string;
}

export default function StyleProfilePage() {
  const router = useRouter();
  const [gender, setGender] = useState("female");

  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastType, setToastType] = useState<"success" | "error">("success");

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);

  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [categories, setCategories] = useState<Categories[]>([]);
  const [sizes, setSizes] = useState<Sizes[]>([]);

  const [selectedCategoryIds, setSelectedCategoryIds] = useState<number[]>([]);
  const [selectedSizeIds, setSelectedSizeIds] = useState<number[]>([]);

  /* ===== Toast ===== */
  const showToast = (msg: string, type: "success" | "error") => {
    setToastMessage(msg);
    setToastType(type);
    setTimeout(() => setToastMessage(null), 3000);
  };

  /* ================= IMAGE UPLOAD ================= */

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file); // ✅ just store file
    setPreview(URL.createObjectURL(file)); // ✅ preview only
  };

  const getOutfit = async () => {
    try {
      setLoading(true);

      const res = await fetch("/api/phase2/get-user-photo", {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("Failed to fetch user photo");
      }

      const data = await res.json();

      console.log("API Response:", data); // optional debug

      if (data?.image_url) {
        setPreview(data.image_url);
        setUploadedImageUrl(data.image_url);
      }
    } catch (err) {
      console.error("Try-on failed", err);
      alert("Try on failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const scanOutfit = async () => {
    if (!selectedFile) return;

    try {
      setLoading(true);

      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch("/api/phase2/save-user-photo", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data?.image_url) {
        setUploadedImageUrl(data.image_url);
        setSelectedFile(null); // 🔥 clear file after upload
      }

      await fetchSaveCategory();
    } catch (err) {
      console.error("Try-on failed", err);
    } finally {
      setLoading(false);
    }
  };

  /* ===== Drag & Drop ===== */
  const handleDrop = (e: React.DragEvent<HTMLLabelElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      setSelectedFile(droppedFile);
      setPreview(URL.createObjectURL(droppedFile));
    }
  };

  const genderOptions = [
    { id: "male", label: "MALE", icon: Mars },
    { id: "female", label: "FEMALE", icon: Venus },
  ];

  const handleGenderChange = (newGender: string) => {
    if (newGender === gender) return;
    setGender(newGender);
    setSelectedCategoryIds([]);
  };

  const fetchSizes = async () => {
    try {
      setLoading(true);

      const res = await fetch("/api/phase2/get-sizes", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ gender }),
      });

      const json = await res.json();

      if (!res.ok || !Array.isArray(json?.data)) {
        console.error("Invalid sizes response:", json);
        setSizes([]);
        return;
      }
      setSizes(json.data);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
      setSizes([]); // prevent crash
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      setLoading(true);

      const res = await fetch("/api/phase2/categories", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ gender }),
      });

      const data = await res.json();

      if (!res.ok || !Array.isArray(data)) {
        console.error("Invalid categories response:", data);
        setCategories([]); // prevent crash
        return;
      }

      setCategories(data);
    } catch (error) {
      console.error("Failed to fetch categories:", error);
      setCategories([]); // prevent crash
    } finally {
      setLoading(false);
    }
  };

  const MAX_SELECTION = 4;
  const MAX_SIZE_SELECTION = 1;

  const toggleCategory = (id: number) => {
    setSelectedCategoryIds((prev) => {
      // If already selected → remove
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }

      // If limit reached → prevent adding
      if (prev.length >= MAX_SELECTION) {
        showToast(`You can select up to ${MAX_SELECTION} categories only`, "error");
        return prev;
      }

      // Otherwise add
      return [...prev, id];
    });
  };

  const toggleSize = (id: number) => {
    setSelectedSizeIds((prev) => {
      // If already selected → remove
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }

      // If limit reached → prevent adding
      if (prev.length >= MAX_SIZE_SELECTION) {
        showToast(`You can select up to ${MAX_SIZE_SELECTION} sizes only`, "error");
        return prev;
      }

      // Otherwise add
      return [...prev, id];
    });
  };

  const fetchSaveCategory = async () => {
    try {
      setLoading(true);

      const payload = {
        gender: gender,
        category_ids: selectedCategoryIds,
      };

      const res = await fetch("/api/phase2/save-categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.message || "Failed to save categories");
      }

      showToast("Profile updated successfully ✨", "success");

    } catch (error) {
      console.error("Save failed:", error);
      showToast("Failed to save profile", "error");
    } finally {
      setLoading(false);
    }
  };

  const fetchGetCategory = async () => {
    try {
      setLoading(true);

      const res = await fetch("/api/phase2/get-categories", {
        method: "GET",
      });

      if (!res.ok) {
        throw new Error("Failed to fetch user photo");
      }

      const result = await res.json();
      console.log("API Response:", result);

      if (result?.data) {
        setGender(result.data.gender ?? "female");
        setSelectedCategoryIds(
          Array.isArray(result.data.category_ids)
            ? result.data.category_ids
            : []
        );
      }
    } catch (err) {
      console.error("Try-on failed", err);
      alert("Try on failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    getOutfit();
    fetchGetCategory();
  }, []);

  useEffect(() => {
    if (gender) {
      fetchCategories();
      fetchSizes();
    }
  }, [gender]);

  return (
    <DashboardLayout>
      <div className="min-h-screen overflow-hidden bg-gradient-to-br from-black via-zinc-900 to-black text-white px-8 pt-8 pb-32">
        {/* Toast Notification */}
        {toastMessage && toastType && (
          <Toast message={toastMessage} type={toastType} />
        )}

        {loading && (
          <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center">
            <Loader size="lg" />
          </div>
        )}

        <div className="max-w-full mx-auto grid lg:grid-cols-2 gap-16">

          {/* LEFT SECTION */}
          <div>
            <h1 className="text-5xl font-bold mb-8 bg-gradient-to-r from-[#FFF5F7] to-[#F3E8FF] bg-clip-text text-transparent opacity-90">
              Create Your <br /> Style Profile.
            </h1>

            <p className="text-zinc-400 mt-4 max-w-md">
              Upload a photo of yourself or a look you love. Our AI analyzes
              your features to curate a personalized high-end wardrobe.
            </p>

            {/* Upload Box */}
            <div className="flex justify-center w-full">
              <label
                htmlFor="fileUpload"
                className={`relative mt-6
                  cursor-pointer border-2 border-dashed rounded-2xl
                  w-full max-w-2xl
                  h-[300px] md:h-[340px] lg:h-[380px]
                  flex items-center justify-center
                  transition-all duration-300
                  overflow-hidden
                  ${isDragging
                    ? "bg-gray-700/80 border-purple-400"
                    : "border-gray-500 text-gray-300 hover:border-purple-500/50"
                  }
      `}
                onDragOver={(e) => {
                  e.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
              >

                {/* Default Background (only when no image) */}
                {!preview && (
                  <>
                    <div
                      className="absolute inset-0 bg-cover bg-center opacity-90"
                      style={{ backgroundImage: "url('/images/upload-bg.png')" }}
                    />
                    <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" />
                  </>
                )}

                {/* Uploaded Image */}
                {preview && (
                  <>
                    <img
                      src={preview}
                      alt="Uploaded Preview"
                      className="absolute inset-0 w-full h-full object-contain"
                    />
                    <div className="absolute inset-0 bg-black/30" />
                  </>
                )}


                {/* UI Content (Only Before Upload) */}
                {!preview && (
                  <div className="relative z-20 text-center flex flex-col items-center px-6">
                    <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-8 border border-white/10 transition-all duration-300">
                      <Camera className="w-8 h-8 text-white/80" />
                    </div>

                    <h2 className="text-2xl font-semibold text-white mb-3 tracking-tight">
                      Drag & Drop Image
                    </h2>

                    <p className="text-zinc-400 text-sm mb-10 tracking-wide">
                      Supports JPG, PNG, WEBP (Max 10MB)
                    </p>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation(); // prevents label double trigger
                        fileInputRef.current?.click();
                      }}
                      className="px-10 py-3 rounded-lg bg-white text-black font-bold text-lg hover:bg-zinc-200 active:scale-95 transition-all shadow-xl">
                      Browse Files
                    </button>
                  </div>
                )}

                {/* Change Image Button (After Upload) */}
                {preview && (
                  <div className="relative z-20">
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation(); // prevents label double trigger
                        fileInputRef.current?.click();
                      }}
                      className="px-10 py-3 rounded-lg bg-white text-black font-bold text-lg hover:bg-zinc-200 active:scale-95 transition-all shadow-xl">
                      Change Image
                    </button>
                  </div>
                )}
              </label>
              <input
                ref={fileInputRef}
                id="fileUpload"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>

            {/* Privacy Note */}
            <div className="mt-6 bg-zinc-900 border border-zinc-800 rounded-xl p-4 text-sm text-zinc-400 flex items-center gap-3">
              {/* Info Icon */}
              <div>
                <Info className="w-4 h-4 text-white-500" />
              </div>
              {/* Text */}
              <p className="leading-relaxed">
                Your photos are used exclusively for style analysis and are never
                shared publicly. We prioritize your privacy as much as your
                aesthetic.
              </p>
            </div>
          </div>

          {/* RIGHT SECTION */}
          <div className="flex flex-col h-full">
            <div className="flex-1 pr-2">

              {/* Gender */}
              <div>
                <h2 className="text-xl font-bold">
                  Select{" "}
                  <span
                    className="bg-[linear-gradient(90deg,#FFFFFF_0%,#F8CEF1_15.49%,#F3A7E5_32.06%,#7DB0D9_46.73%)] 
                   bg-clip-text text-transparent"
                  >
                    Gender
                  </span>
                </h2>
                <p className="text-zinc-400 text-sm mt-1">
                  Choose your preferred Gender.
                </p>

                <div className="flex gap-4 mt-6 ml-1 mr-1">
                  {genderOptions.map((g) => {
                    const Icon = g.icon;
                    const isActive = gender === g.id;

                    return (
                      <button
                        key={g.id}
                        onClick={() => handleGenderChange(g.id)}
                        className="relative group transition-all duration-300 outline-none"
                      >
                        {/* Animated Gradient Border (visible only when active) */}
                        <div
                          className={`absolute -inset-[1px] rounded-[1rem] transition-opacity duration-300 ${isActive ? "opacity-100" : "opacity-0"
                            }`}
                          style={{
                            background: "linear-gradient(to right, #BC3CD3, #7116E3)",
                          }}
                        />

                        {/* Main Button Container */}
                        <div
                          className={`relative flex flex-col items-center justify-center w-48 h-16 rounded-[1rem] transition-all duration-300 ${isActive
                            ? "bg-[#141211] text-white"
                            : "bg-[#1A1817] border border-zinc-800 text-zinc-400 hover:border-zinc-700"
                            }`}
                        >
                          {/* Active Checkmark Icon */}
                          {isActive && (
                            <div className="absolute top-3 right-4 animate-in fade-in zoom-in duration-300">
                              <CheckCircle2 className="w-5 h-5 text-[#BC3CD3]" />
                            </div>
                          )}

                          <Icon className={`w-6 h-6 mb-2 transition-colors ${isActive ? "text-[#BC3CD3]" : "text-zinc-500"
                            }`} />

                          <span className={`text-sm font-semibold tracking-[0.15em] transition-colors ${isActive ? "bg-gradient-to-r from-[#BC3CD3] to-[#7116E3] bg-clip-text text-transparent" : "text-zinc-400"
                            }`}>
                            {g.label}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Size */}
              <div className="mt-6">
                <h2 className="text-xl font-bold">
                  Select{" "}
                  <span
                    className="bg-[linear-gradient(90deg,#FFFFFF_0%,#F8CEF1_15.49%,#F3A7E5_32.06%,#7DB0D9_46.73%)] 
                   bg-clip-text text-transparent"
                  >
                    Size
                  </span>
                </h2>
                <p className="text-zinc-400 text-sm mt-1">
                  Choose your standard sizing preference.
                </p>

                <div className="flex flex-wrap gap-4 mt-6">
                  {sizes.map((item) => {
                    const isSelected = selectedSizeIds.includes(item.id);
                    const isDisabled =
                      !isSelected && selectedSizeIds.length >= MAX_SIZE_SELECTION;

                    return (
                      <button
                        key={item.id}
                        onClick={() => {
                          if (!isDisabled) toggleSize(item.id);
                        }}
                        disabled={isDisabled}
                        className={`
                          px-8 py-3 rounded-xl font-semibold tracking-wide
                          transition-all duration-300
                          ${isSelected
                            ? "bg-gradient-to-r from-fuchsia-500 to-purple-600 text-white"
                            : "bg-zinc-900 text-white border border-zinc-700 hover:border-zinc-500"
                          }
                          ${isDisabled ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}
                        `}
                      >
                        {item.name.toUpperCase()}
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Aesthetic */}
              <div className="mt-6">
                <h2 className="text-xl font-bold">
                  Select{" "}
                  <span
                    className="bg-[linear-gradient(90deg,#FFFFFF_0%,#F8CEF1_15.49%,#F3A7E5_32.06%,#7DB0D9_46.73%)] 
                   bg-clip-text text-transparent"
                  >
                    Your Aesthetic
                  </span>
                </h2>
                <p className="text-zinc-400 text-sm mt-1">
                  Choose the silhouettes and vibes that resonate with your
                  personal brand.
                </p>

                <div className="p-4 h-full md:h-full lg:h-full">
                  <div className="grid sm:grid-cols-3 gap-6">
                    {categories.map((item) => {
                      const isSelected = selectedCategoryIds.includes(item.id);
                      const isDisabled = !isSelected && selectedCategoryIds.length >= MAX_SELECTION;

                      return (
                        <div
                          key={item.id}
                          onClick={() => {
                            if (!isDisabled) toggleCategory(item.id);
                          }}
                          className={`cursor-pointer rounded-2xl overflow-hidden border transition-all ${isSelected
                            ? "border-purple-500 shadow-lg shadow-purple-500/20"
                            : isDisabled
                              ? "border-zinc-800 opacity-40 cursor-not-allowed"
                              : "border-zinc-800 hover:border-zinc-600"
                            }`}
                        >
                          <div className="relative h-50">
                            <img
                              src={item.image_url}
                              alt={item.name}
                              className="absolute inset-0 w-full h-full object-cover"
                            />
                            {isSelected && (
                              <div className="absolute top-3 right-4 animate-in fade-in zoom-in duration-300">
                                <CheckCircle2 className="w-5 h-5 text-[#BC3CD3] drop-shadow-md" />
                              </div>
                            )}
                          </div>

                          <div className="p-4 bg-black">
                            <h4 className="font-semibold">{item.name}</h4>
                            <p className="text-xs text-zinc-400 mt-1 uppercase tracking-wider">
                              {item.description}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

            </div>

          </div>

        </div>
        {/* Bottom Right Floating Action Area */}
        <div className="fixed bottom-0 right-0 w-full z-50">

          {/* Background Layer */}
          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/95 to-transparent backdrop-blur-md" />

          {/* Button Container */}
          <div className="relative flex justify-end px-8 py-6">
            <button
              className="
        relative px-8 py-3 rounded-lg font-bold text-black
        bg-white
        overflow-hidden
        transition-all duration-300
        hover:scale-[1.02]
        shadow-2xl
      "
              onClick={(e) => {
                e.stopPropagation();

                if (!preview) {
                  showToast("Please upload an image first", "error");
                  return;
                }

                if (selectedCategoryIds.length === 0) {
                  showToast("Please select at least one category", "error");
                  return;
                }

                if (selectedFile) {
                  scanOutfit();
                } else {
                  fetchSaveCategory();
                }
              }}
            >
              <span
                className="absolute inset-0 rounded-lg opacity-70 pointer-events-none"
                style={{
                  background:
                    "linear-gradient(96.23deg, rgba(255, 54, 218, 0.4) 25.63%, rgba(178, 84, 227, 0.4) 42.31%, rgba(37, 140, 244, 0.4) 87.7%)",
                }}
              />

              <span className="relative z-10">Let’s Get Styled</span>
            </button>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
