"use client";

import Image from "next/image";
import { useState } from "react";
import { useShared } from "./DataProvider";

function photo(url: string, size: number) {
  return url.replace("/1col/", size <= 44 ? "/1col/" : size <= 100 ? "/2col/" : "/4col/");
}

function isLight(hex: string) {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
  return 0.299 * r + 0.587 * g + 0.114 * b > 150;
}

export function Avatar({
  code,
  color,
  size = 40,
  className = "rounded-full",
}: {
  code: string;
  color: string;
  size?: number;
  className?: string;
}) {
  const { people } = useShared();
  const [failed, setFailed] = useState<string | null>(null);
  const person = people[code];
  const src = person?.headshot ? photo(person.headshot, size) : null;

  return (
    <span
      className={`relative inline-grid shrink-0 place-items-center overflow-hidden ${className}`}
      style={{
        width: size,
        height: size,
        background: `radial-gradient(circle at 50% 28%, ${color}, color-mix(in srgb, ${color} 30%, #0d0d0d) 78%)`,
      }}
    >
      {src && failed !== src ? (
        <Image
          src={src}
          alt={person.name}
          fill
          sizes={`${size}px`}
          className="object-cover object-top"
          onError={() => setFailed(src)}
        />
      ) : (
        <span
          className="font-display font-bold"
          style={{ fontSize: size * 0.32, color: isLight(color) ? "#0d0d0d" : "#ffffff" }}
        >
          {code}
        </span>
      )}
    </span>
  );
}
