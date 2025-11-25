import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

export default function AdminLoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [otpCode, setOtpCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [otpSent, setOtpSent] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  const handleRequestOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    toast.loading("Sending OTP code...", { id: "otp-request-toast" });

    try {
      const response = await fetch('/api/auth/login/request-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to send OTP');
      }

      setOtpSent(true);
      setUserEmail(email);
      toast.success("OTP Sent!", { 
        id: "otp-request-toast", 
        description: "Check your email for the 6-digit code"
      });
      
    } catch (error: any) {
      console.error("OTP request error:", error);
      const errorMessage = error.message || "Failed to send OTP. Please try again.";
      setError(errorMessage);
      toast.error("OTP Request Failed", { id: "otp-request-toast", description: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);
    toast.loading("Verifying OTP code...", { id: "otp-verify-toast" });

    try {
      const response = await fetch('/api/auth/login/verify-otp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: userEmail,
          otp_code: otpCode,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'OTP verification failed');
      }

      // Store JWT token in localStorage
      localStorage.setItem('jwt_token', data.access_token);
      localStorage.setItem('user_email', data.user.email);
      
      console.log("OTP verification successful");
      toast.success("Login Successful!", { 
        id: "otp-verify-toast", 
        description: "Redirecting to admin dashboard..."
      });
      
      navigate("/admin-dashboard-page");
      
    } catch (error: any) {
      console.error("OTP verification error:", error);
      const errorMessage = error.message || "Invalid or expired OTP code. Please try again.";
      setError(errorMessage);
      toast.error("OTP Verification Failed", { id: "otp-verify-toast", description: errorMessage });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToEmail = () => {
    setOtpSent(false);
    setOtpCode("");
    setError("");
  };

  const handleResendOTP = () => {
    setOtpCode("");
    setError("");
    const form = document.createElement('form');
    form.onsubmit = handleRequestOTP;
    handleRequestOTP({ preventDefault: () => {} } as React.FormEvent);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-sm shadow-xl">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-serif">
            {otpSent ? "Enter Verification Code" : "Admin Login"}
          </CardTitle>
          <CardDescription>
            {otpSent 
              ? "Enter the 6-digit code sent to your email" 
              : "Enter your email to receive a login code"}
          </CardDescription>
        </CardHeader>
        
        {!otpSent ? (
          // Email input form
          <form onSubmit={handleRequestOTP}>
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
                  autoFocus
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
                {isLoading ? "Sending code..." : "Send Login Code"}
              </Button>
            </CardFooter>
          </form>
        ) : (
          // OTP verification form
          <form onSubmit={handleVerifyOTP}>
            <CardContent className="space-y-4">
              <div className="text-sm text-muted-foreground text-center">
                Code sent to: <strong>{userEmail}</strong>
              </div>
              <div className="space-y-2">
                <Label htmlFor="otpCode">Verification Code</Label>
                <Input
                  id="otpCode"
                  type="text"
                  placeholder="000000"
                  value={otpCode}
                  onChange={(e) => {
                    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setOtpCode(value);
                  }}
                  maxLength={6}
                  required
                  disabled={isLoading}
                  className="text-center text-lg tracking-widest font-mono"
                  autoFocus
                />
                <p className="text-xs text-muted-foreground text-center">
                  Enter the 6-digit code from your email
                </p>
              </div>
              {error && (
                <p className="text-sm text-destructive text-center bg-destructive/10 p-2 rounded-md">
                  {error}
                </p>
              )}
            </CardContent>
            <CardFooter className="flex-col space-y-2">
              <Button type="submit" className="w-full" disabled={isLoading || otpCode.length !== 6}>
                {isLoading ? "Verifying..." : "Verify & Login"}
              </Button>
              <div className="flex gap-2 w-full">
                <Button 
                  type="button" 
                  variant="outline" 
                  className="flex-1" 
                  onClick={handleBackToEmail}
                  disabled={isLoading}
                >
                  Change Email
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  className="flex-1" 
                  onClick={handleResendOTP}
                  disabled={isLoading}
                >
                  Resend Code
                </Button>
              </div>
            </CardFooter>
          </form>
        )}
      </Card>
    </div>
  );
}
