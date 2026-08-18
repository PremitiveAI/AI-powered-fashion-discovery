"use client";
import React from 'react';

interface ButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  className?: string;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ children, onClick, className = '', disabled = false,
}) => {
      const gradientStyles = `
        h-12 min-w-[150px] py-3 mt-4
        bg-gradient-to-r
        from-purple-400 to-purple-900
        text-[16px] text-white
        font-bold px-6 rounded-full
        shadow-lg hover:scale-105
        border border-2 border-gray-400
        hover:border-purple-500
        transition-all mx-auto block
        duration-300 ease-in-out
        text-center whitespace-normal
      `.trim().replace(/\s+/g, " ");


  const disabledStyles = disabled
    ? 'opacity-50 cursor-not-allowed bg-gray-500 hover:scale-100 hover:border-gray-400 shadow-none'
    : '';

  return (
    <button
      onClick={!disabled ? onClick : undefined}
      disabled={disabled}
      className={`${gradientStyles} ${disabledStyles} ${className}`}
    >
      {children}
    </button>
  );
};