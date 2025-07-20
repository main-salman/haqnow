import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { 
  AlertDialog, 
  AlertDialogAction, 
  AlertDialogCancel, 
  AlertDialogContent, 
  AlertDialogDescription, 
  AlertDialogFooter, 
  AlertDialogHeader, 
  AlertDialogTitle, 
  AlertDialogTrigger 
} from "@/components/ui/alert-dialog";
import { 
  Users, 
  UserPlus, 
  Shield, 
  ShieldCheck, 
  Trash2, 
  Loader2, 
  Eye, 
  EyeOff,
  Key,
  Download
} from "lucide-react";

interface Admin {
  id: number;
  email: string;
  name: string;
  two_factor_enabled: boolean;
  is_active: boolean;
  is_super_admin: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  last_login_at: string | null;
}

export default function AdminManagementPage() {
  const navigate = useNavigate();
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAddingAdmin, setIsAddingAdmin] = useState(false);
  const [currentUserEmail] = useState(localStorage.getItem('user_email') || '');
  
  // Add admin form state
  const [newAdminEmail, setNewAdminEmail] = useState('');
  const [newAdminName, setNewAdminName] = useState('');
  const [newAdminPassword, setNewAdminPassword] = useState('');
  const [newAdminRole, setNewAdminRole] = useState('admin');
  const [showPassword, setShowPassword] = useState(false);
  
  // 2FA setup state
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [backupCodes, setBackupCodes] = useState<string[]>([]);
  const [is2FAEnabled, setIs2FAEnabled] = useState(false);

  // Check if current user is super admin
  const isCurrentUserSuperAdmin = () => {
    const currentAdmin = admins.find(admin => admin.email === currentUserEmail);
    return currentAdmin?.is_super_admin || false;
  };

  // Check if current user has 2FA enabled
  const currentUserHas2FA = () => {
    const currentAdmin = admins.find(admin => admin.email === currentUserEmail);
    return currentAdmin?.two_factor_enabled || false;
  };

  // Fetch admins list
  const fetchAdmins = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/admin-management/admins', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setAdmins(data.admins || []);
      setIs2FAEnabled(currentUserHas2FA());
    } catch (error: any) {
      console.error('Error fetching admins:', error);
      alert('Failed to fetch admin list. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  // Add new admin
  const handleAddAdmin = async () => {
    if (!newAdminEmail || !newAdminName || !newAdminPassword) {
      alert('Please fill in all fields');
      return;
    }

    setIsAddingAdmin(true);
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/admin-management/admins', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          email: newAdminEmail,
          name: newAdminName,
          password: newAdminPassword,
          is_super_admin: newAdminRole === 'super_admin',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create admin');
      }

      // Clear form and refresh list
      setNewAdminEmail('');
      setNewAdminName('');
      setNewAdminPassword('');
      setNewAdminRole('admin');
      await fetchAdmins();
      alert('Admin added successfully!');
    } catch (error: any) {
      console.error('Error adding admin:', error);
      alert(error.message || 'Failed to add admin. Please try again.');
    } finally {
      setIsAddingAdmin(false);
    }
  };

  // Delete admin
  const handleDeleteAdmin = async (adminId: number, adminEmail: string) => {
    if (adminEmail === currentUserEmail) {
      alert("You cannot delete yourself!");
      return;
    }

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(`/api/admin-management/admins/${adminId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete admin');
      }

      await fetchAdmins();
      alert('Admin deleted successfully!');
    } catch (error: any) {
      console.error('Error deleting admin:', error);
      alert(error.message || 'Failed to delete admin. Please try again.');
    }
  };

  // Setup 2FA
  const handleSetup2FA = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/admin-management/2fa/setup', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to setup 2FA');
      }

      const data = await response.json();
      setQrCodeUrl(data.qr_code_url);
      setShow2FASetup(true);
    } catch (error: any) {
      console.error('Error setting up 2FA:', error);
      alert('Failed to setup 2FA. Please try again.');
    }
  };

  // Verify and enable 2FA
  const handleVerify2FA = async () => {
    if (!verificationCode) {
      alert('Please enter the verification code');
      return;
    }

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/admin-management/2fa/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          code: verificationCode,
        }),
      });

      if (!response.ok) {
        throw new Error('Invalid verification code');
      }

      const data = await response.json();
      setBackupCodes(data.backup_codes || []);
      setIs2FAEnabled(true);
      await fetchAdmins();
      alert('2FA enabled successfully! Please save your backup codes.');
    } catch (error: any) {
      console.error('Error verifying 2FA:', error);
      alert('Invalid verification code. Please try again.');
    }
  };

  // Disable 2FA
  const handleDisable2FA = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch('/api/admin-management/2fa/disable', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to disable 2FA');
      }

      setIs2FAEnabled(false);
      setShow2FASetup(false);
      setQrCodeUrl('');
      setVerificationCode('');
      setBackupCodes([]);
      await fetchAdmins();
      alert('2FA disabled successfully!');
    } catch (error: any) {
      console.error('Error disabling 2FA:', error);
      alert('Failed to disable 2FA. Please try again.');
    }
  };

  // Download backup codes
  const downloadBackupCodes = () => {
    const text = backupCodes.join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'haqnow-2fa-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    fetchAdmins();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary font-serif">Admin Management</h1>
          <p className="text-muted-foreground">Manage administrator accounts and security settings</p>
        </div>
      </div>

      {/* 2FA Management Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Two-Factor Authentication (2FA)
          </CardTitle>
          <CardDescription>
            Enhance your account security with two-factor authentication
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {currentUserHas2FA() ? (
                <>
                  <ShieldCheck className="h-5 w-5 text-green-600" />
                  <span className="text-green-600 font-medium">2FA Enabled</span>
                </>
              ) : (
                <>
                  <Shield className="h-5 w-5 text-orange-600" />
                  <span className="text-orange-600 font-medium">2FA Disabled</span>
                </>
              )}
            </div>
            <div className="flex gap-2">
              {!currentUserHas2FA() ? (
                <Button onClick={handleSetup2FA}>
                  <Key className="h-4 w-4 mr-2" />
                  Setup 2FA
                </Button>
              ) : (
                <Button variant="outline" onClick={handleDisable2FA}>
                  Disable 2FA
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Add New Admin Section - Only for Super Admins */}
      {isCurrentUserSuperAdmin() && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <UserPlus className="h-5 w-5" />
              Add New Administrator
            </CardTitle>
            <CardDescription>
              Create a new administrator account (Super Admin only)
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="newAdminEmail">Email Address</Label>
                <Input
                  id="newAdminEmail"
                  type="email"
                  value={newAdminEmail}
                  onChange={(e) => setNewAdminEmail(e.target.value)}
                  placeholder="admin@example.com"
                />
              </div>
              <div>
                <Label htmlFor="newAdminName">Full Name</Label>
                <Input
                  id="newAdminName"
                  type="text"
                  value={newAdminName}
                  onChange={(e) => setNewAdminName(e.target.value)}
                  placeholder="Admin Name"
                />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="newAdminPassword">Password</Label>
                <div className="relative">
                  <Input
                    id="newAdminPassword"
                    type={showPassword ? "text" : "password"}
                    value={newAdminPassword}
                    onChange={(e) => setNewAdminPassword(e.target.value)}
                    placeholder="••••••••"
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
              <div>
                <Label htmlFor="newAdminRole">Role</Label>
                <select
                  id="newAdminRole"
                  value={newAdminRole}
                  onChange={(e) => setNewAdminRole(e.target.value)}
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <option value="admin">Admin</option>
                  <option value="super_admin">Super Admin</option>
                </select>
              </div>
            </div>
            <Button 
              onClick={handleAddAdmin} 
              disabled={isAddingAdmin}
              className="w-full md:w-auto"
            >
              {isAddingAdmin ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <UserPlus className="h-4 w-4 mr-2" />
              )}
              Add Administrator
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Current Administrators List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            Current Administrators ({admins.length})
          </CardTitle>
          <CardDescription>
            List of all administrator accounts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {admins.map((admin) => (
              <div key={admin.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-medium">{admin.name}</h3>
                    {admin.email === currentUserEmail && (
                      <Badge variant="secondary">You</Badge>
                    )}
                    <Badge variant={admin.is_super_admin ? 'default' : 'outline'}>
                      {admin.is_super_admin ? 'Super Admin' : 'Admin'}
                    </Badge>
                    {admin.two_factor_enabled && (
                      <Badge variant="secondary" className="text-green-600">
                        <ShieldCheck className="h-3 w-3 mr-1" />
                        2FA
                      </Badge>
                    )}
                  </div>
                  <p className="text-sm text-muted-foreground">{admin.email}</p>
                  <p className="text-xs text-muted-foreground">
                    Created: {new Date(admin.created_at).toLocaleDateString()}
                    {admin.last_login_at && (
                      <> • Last login: {new Date(admin.last_login_at).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
                {isCurrentUserSuperAdmin() && admin.email !== currentUserEmail && (
                  <AlertDialog>
                    <AlertDialogTrigger asChild>
                      <Button variant="outline" size="sm">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </AlertDialogTrigger>
                    <AlertDialogContent>
                      <AlertDialogHeader>
                        <AlertDialogTitle>Delete Administrator</AlertDialogTitle>
                        <AlertDialogDescription>
                          Are you sure you want to delete the administrator "{admin.name}" ({admin.email})? 
                          This action cannot be undone.
                        </AlertDialogDescription>
                      </AlertDialogHeader>
                      <AlertDialogFooter>
                        <AlertDialogCancel>Cancel</AlertDialogCancel>
                        <AlertDialogAction 
                          onClick={() => handleDeleteAdmin(admin.id, admin.email)}
                          className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                        >
                          Delete
                        </AlertDialogAction>
                      </AlertDialogFooter>
                    </AlertDialogContent>
                  </AlertDialog>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* 2FA Setup Modal */}
      {show2FASetup && (
        <AlertDialog open={show2FASetup} onOpenChange={setShow2FASetup}>
          <AlertDialogContent className="max-w-md">
            <AlertDialogHeader>
              <AlertDialogTitle>Setup Two-Factor Authentication</AlertDialogTitle>
              <AlertDialogDescription>
                Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="space-y-4">
              {qrCodeUrl && (
                <div className="flex justify-center">
                  <img src={qrCodeUrl} alt="2FA QR Code" className="w-48 h-48" />
                </div>
              )}
              <div>
                <Label htmlFor="verificationCode">Verification Code</Label>
                <Input
                  id="verificationCode"
                  type="text"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value)}
                  placeholder="Enter 6-digit code"
                  maxLength={6}
                />
              </div>
              {backupCodes.length > 0 && (
                <div className="p-4 bg-muted rounded-lg">
                  <h4 className="font-medium mb-2">Backup Codes</h4>
                  <p className="text-sm text-muted-foreground mb-2">
                    Save these codes in a safe place. You can use them to access your account if you lose your authenticator device.
                  </p>
                  <div className="grid grid-cols-2 gap-1 text-xs font-mono">
                    {backupCodes.map((code, index) => (
                      <div key={index}>{code}</div>
                    ))}
                  </div>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={downloadBackupCodes}
                    className="mt-2"
                  >
                    <Download className="h-4 w-4 mr-2" />
                    Download Codes
                  </Button>
                </div>
              )}
            </div>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={handleVerify2FA}>
                Verify & Enable 2FA
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}
    </div>
  );
} 