import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner"; // For displaying notifications

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  
  // 2FA state
  const [requires2FA, setRequires2FA] = useState(false);
  const [twoFactorToken, setTwoFactorToken] = useState("");
  const [userEmail, setUserEmail] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    toast.loading("Attempting to log in...", { id: "login-toast" });

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      // Check if 2FA is required
      if (data.requires_2fa) {
        setRequires2FA(true);
        setUserEmail(data.email);
        toast.info("2FA Required", { 
          id: "login-toast", 
          description: "Please enter your 2FA code"
        });
        return;
      }

      // Normal login (no 2FA) - store JWT token
      localStorage.setItem('jwt_token', data.access_token);
      localStorage.setItem('user_email', data.user.email);
      
      // Security: Remove sensitive logging - only log success without user data
      console.log("Admin login successful");
      toast.success("Login Successful!", { 
        id: "login-toast", 
        description: "Redirecting to admin dashboard..."
      });
      
      navigate("/admin-dashboard-page");
      
    } catch (error: any) {
      console.error("Login error:", error);
      const errorMessage = error.message === "Incorrect email or password" 
        ? "Invalid email or password. Please try again."
        : "An error occurred during login. Please try again later.";
      setError(errorMessage);
      toast.error("Login Failed", { id: "login-toast", description: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify2FA = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    toast.loading("Verifying 2FA code...", { id: "2fa-toast" });

    try {
      const response = await fetch('/api/auth/login/verify-2fa', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          token: twoFactorToken,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || '2FA verification failed');
      }

      // Store JWT token in localStorage
      localStorage.setItem('jwt_token', data.access_token);
      localStorage.setItem('user_email', data.user.email);
      
      console.log("2FA verification successful");
      toast.success("2FA Verified!", { 
        id: "2fa-toast", 
        description: "Redirecting to admin dashboard..."
      });
      
      navigate("/admin-dashboard-page");
      
    } catch (error: any) {
      console.error("2FA verification error:", error);
      const errorMessage = error.message || "Invalid 2FA code. Please try again.";
      setError(errorMessage);
      toast.error("2FA Failed", { id: "2fa-toast", description: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    setRequires2FA(false);
    setTwoFactorToken("");
    setUserEmail("");
    setError("");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-serif">
            {requires2FA ? "Two-Factor Authentication" : "Admin Login"}
          </CardTitle>
          <CardDescription>
            {requires2FA 
              ? "Enter your 6-digit authentication code" 
              : "Access the HaqNow Admin Panel"}
          </CardDescription>
        </CardHeader>
        
        {!requires2FA ? (
          // Regular login form
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
        ) : (
          // 2FA verification form
          <form onSubmit={handleVerify2FA}>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground text-center">
                Logged in as: <strong>{userEmail}</strong>
              </div>
              <div className="space-y-2">
                <Label htmlFor="twoFactorToken">Authentication Code</Label>
                <Input
                  id="twoFactorToken"
                  type="text"
                  placeholder="000000"
                  value={twoFactorToken}
                  onChange={(e) => setTwoFactorToken(e.target.value)}
                  maxLength={6}
                  required
                  disabled={isLoading}
                  className="text-center text-lg tracking-widest"
                />
              </div>
              {error && (
                <p className="text-sm text-destructive text-center bg-destructive/10 p-2 rounded-md">
                  {error}
                </p>
              )}
            </CardContent>
            <CardFooter className="flex-col space-y-2">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Verifying..." : "Verify"}
              </Button>
              <Button 
                type="button" 
                variant="outline" 
                className="w-full" 
                onClick={handleBackToLogin}
                disabled={isLoading}
              >
                Back to Login
              </Button>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  );
}
