import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { supabase } from "utils/supabaseClient"; // Import Supabase client
import { toast } from "sonner"; // For displaying notifications

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false); // Added for loading state

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    toast.loading("Attempting to log in...", { id: "login-toast" });

    const { data, error: supaError } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    setIsLoading(false);

    if (supaError) {
      console.error("Supabase login error:", supaError);
      const errorMessage = supaError.message === "Invalid login credentials" 
        ? "Invalid email or password. Please try again."
        : "An error occurred during login. Please try again later.";
      setError(errorMessage);
      toast.error("Login Failed", { id: "login-toast", description: errorMessage });
    } else if (data.user) {
      // Check if the user is an admin (requires user_profiles table and RLS setup)
      // For now, we will assume any successful login via this page is an admin intent
      // and rely on RLS on the backend to protect admin-only resources.
      // A more robust check would query the user_profiles table for an is_admin flag.
      console.log("Supabase login successful:", data.user);
      toast.success("Login Successful!", { 
        id: "login-toast", 
        description: "Redirecting to admin dashboard..."
      });
      
      // Store session or user data if needed globally (e.g., Zustand store)
      // Example: useAuthStore.getState().setUser(data.user);
      
      navigate("/admin-dashboard-page");
    } else {
      // Should not happen if supaError is null and data.user is null, but as a fallback
      setError("An unexpected error occurred. Please try again.");
      toast.error("Login Error", { id: "login-toast", description: "An unexpected error occurred." });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-serif">Admin Login</CardTitle>
          <CardDescription>Access the FOIArchive Admin Panel</CardDescription>
        </CardHeader>
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            {error && (
              <p className="text-sm text-destructive text-center bg-destructive/10 p-2 rounded-md">
                {error}
              </p>
            )}
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Logging in..." : "Login"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
