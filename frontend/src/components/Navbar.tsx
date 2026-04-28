"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Menu,
  X,
  Home,
  Upload,
  LayoutDashboard,
  Brain,
  FileText,
} from "lucide-react";

import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from "@clerk/nextjs";

export default function Navbar() {
  const [open, setOpen] = useState(false);

  function closeMenu() {
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-black/70 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">

        {/* Logo */}
        <Link
          href="/"
          onClick={closeMenu}
          className="text-2xl font-bold tracking-wide"
        >
          FairLens
        </Link>

        {/* Right Side */}
        <div className="flex items-center gap-3">

          {/* Signed Out */}
          <SignedOut>
            <SignInButton mode="modal">
              <button className="px-4 py-2 rounded-xl bg-cyan-500 text-black font-semibold hover:bg-cyan-400 transition">
                Sign In
              </button>
            </SignInButton>
          </SignedOut>

          {/* Signed In */}
          <SignedIn>
            <UserButton afterSignOutUrl="/" />
          </SignedIn>

          {/* Hamburger */}
          <button
            onClick={() => setOpen(!open)}
            className="p-2 rounded-xl border border-slate-700 hover:bg-slate-800 transition"
          >
            {open ? <X size={22} /> : <Menu size={22} />}
          </button>

        </div>
      </div>

      {/* Dropdown Menu */}
      {open && (
        <div className="px-6 pb-4 pt-3 space-y-3 bg-slate-950 border-t border-slate-800">

          <NavItem
            href="/"
            icon={<Home size={16} />}
            label="Home"
            onClick={closeMenu}
          />

          <NavItem
            href="/upload"
            icon={<Upload size={16} />}
            label="Upload"
            onClick={closeMenu}
          />

          <NavItem
            href="/dashboard"
            icon={<LayoutDashboard size={16} />}
            label="Dashboard"
            onClick={closeMenu}
          />

          <NavItem
            href="/explainability"
            icon={<Brain size={16} />}
            label="Explainability"
            onClick={closeMenu}
          />

          <a
            href="http://127.0.0.1:8000/api/v1/report/pdf"
            target="_blank"
            onClick={closeMenu}
            className="flex items-center gap-2 text-slate-300 hover:text-white transition"
          >
            <FileText size={16} />
            PDF Report
          </a>

        </div>
      )}
    </header>
  );
}

function NavItem({
  href,
  icon,
  label,
  onClick,
}: any) {
  return (
    <Link
      href={href}
      onClick={onClick}
      className="flex items-center gap-2 text-slate-300 hover:text-white transition"
    >
      {icon}
      {label}
    </Link>
  );
}