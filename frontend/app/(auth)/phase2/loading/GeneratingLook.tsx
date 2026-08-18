"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Check } from "lucide-react";

export default function GeneratingLook({ id }: { id: number | null }) {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [dots, setDots] = useState("");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length >= 3 ? "" : prev + "."));
    }, 500);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
  const timer1 = setTimeout(() => setStep(2), 2000);
  const timer2 = setTimeout(() => setStep(3), 4000);
  const timer3 = id
    ? setTimeout(() => {
        // router.push(`/phase2/look-detail?id=${id}`);
      }, 6000)
    : null;

  return () => {
    clearTimeout(timer1);
    clearTimeout(timer2);
    if (timer3) clearTimeout(timer3);
  };
}, [router, id]);

  useEffect(() => {
  if (step === 3 && id) {
    const redirectTimer = setTimeout(() => {
    //   router.push(`/phase2/look-detail?id=${id}`);
    }, 2000);
    return () => clearTimeout(redirectTimer);
  }
}, [step, router, id]);

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-blue-500/20 rounded-full blur-[120px]" />
      <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[140px]" />

      <div className="relative z-10 flex flex-col items-center">
        <div className="relative mb-8">
          <div className="w-36 h-36 rounded-full border border-purple-500/40 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-blue-500 border-r-purple-500 animate-spin" />
            <Sparkles className="w-10 h-10 text-purple-400" />
          </div>
        </div>

        <h1 className="text-3xl font-semibold text-white">
          Generating your look
          <span className="text-blue-400">{dots}</span>
        </h1>

        <p className="mt-3 text-sm tracking-[0.3em] text-gray-400 uppercase">
          Updating Composition
        </p>

        <div className="w-56 h-[3px] bg-gray-700 mt-4 rounded-full overflow-hidden">
          <div className="h-full w-2/3 bg-gradient-to-r from-blue-500 to-purple-500 animate-pulse" />
        </div>

        <div className="mt-12 space-y-4 w-[420px]">
          <StepCard number={1} text="Analyzing body type & preferences" active={step === 1} completed={step > 1} />
          <StepCard number={2} text="Matching seasonal color palette" active={step === 2} completed={step > 2} inProgress={step === 2} />
          <StepCard number={3} text="Finalizing curated selection" active={step === 3} />
        </div>
      </div>
    </div>
  );
}

function StepCard({
  number, text, active, completed, inProgress,
}: {
  number: number;
  text: string;
  active?: boolean;
  completed?: boolean;
  inProgress?: boolean;
}) {
  return (
    <div className={`flex items-center justify-between px-6 py-4 rounded-xl border transition-all duration-300 backdrop-blur-md ${active ? "border-blue-500 bg-white/5" : "border-white/10 bg-white/5 opacity-60"}`}>
      <div className="flex items-center gap-4">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${completed ? "bg-blue-600 text-white" : active ? "bg-blue-600/30 text-blue-400" : "bg-white/10 text-gray-400"}`}>
          {completed ? <Check size={18} /> : number}
        </div>
        <span className="text-sm text-white">{text}</span>
      </div>
      {inProgress && (
        <span className="text-xs text-blue-400 font-medium tracking-widest">IN PROGRESS</span>
      )}
    </div>
  );
}