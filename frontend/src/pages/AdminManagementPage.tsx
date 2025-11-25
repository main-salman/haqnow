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
  Trash2, 
  Loader2, 
  Megaphone,
  Plus,
  ToggleLeft,
  ToggleRight,
  Copy
} from "lucide-react";

interface Admin {
  id: number;
  email: string;
  name: string;
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
  const [newAdminRole, setNewAdminRole] = useState('admin');

  // Announcement banner state
  const [announcementEnabled, setAnnouncementEnabled] = useState(false);
  const [announcementContent, setAnnouncementContent] = useState("");
  const [isSavingAnnouncement, setIsSavingAnnouncement] = useState(false);
  
  // Upload notification recipients
  const [notificationEmails, setNotificationEmails] = useState<string[]>([]);
  const [newNotificationEmail, setNewNotificationEmail] = useState("");
  
  // API Keys state (Super Admin only)
  interface ApiKey {
    id: number;
    name: string;
    key_prefix: string;
    scopes: string[];
    is_active: boolean;
    created_by: string | null;
    created_at: string;
    last_used_at: string | null;
    usage_count: number;
    plaintext_key?: string | null; // only returned at creation time
  }
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [isLoadingApiKeys, setIsLoadingApiKeys] = useState(false);
  const [newApiKeyName, setNewApiKeyName] = useState("");
  const [newApiKeyScopes, setNewApiKeyScopes] = useState<string[]>(["upload", "download"]);
  const [isCreatingApiKey, setIsCreatingApiKey] = useState(false);
  const [justCreatedKey, setJustCreatedKey] = useState<ApiKey | null>(null);

  // Check if current user is super admin
  const isCurrentUserSuperAdmin = () => {
    // Debug: log the current state
    console.log('Checking super admin status:', {
      currentUserEmail,
      adminsCount: admins.length,
      admins: admins.map(a => ({ email: a.email, is_super_admin: a.is_super_admin }))
    });
    
    const currentAdmin = admins.find(admin => admin.email === currentUserEmail);
    const isSuperAdmin = currentAdmin?.is_super_admin || false;
    
    console.log('Super admin result:', { currentAdmin, isSuperAdmin });
    return isSuperAdmin;
  };


  // Fetch current user's own admin info (for regular admins)
  const fetchCurrentUserInfo = async () => {
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) return null;
      
      const response = await fetch('/api/admin-management/me', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        console.log('👤 Current user info:', userData);
        
        // Set the current user as the only admin in the array for regular admins
        if (admins.length === 0) {
          setAdmins([userData]);
        }
        
        return userData;
      }
    } catch (error) {
      console.log('ℹ️ Could not fetch current user info (normal for super admins)');
    }
    return null;
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
        if (response.status === 401) {
          // Unauthorized - redirect to login
          navigate("/admin-login-page");
          return;
        }
        if (response.status === 403) {
          // Forbidden - regular admin, show limited functionality
          console.log('🔒 Regular admin detected - showing limited functionality');
          setAdmins([]); // Empty array for regular admins
          
          // Try to get current user's own info
          await fetchCurrentUserInfo();
          return; // Don't throw error, just continue with limited functionality
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log('🔍 API Response:', data);
      setAdmins(data || []);
    } catch (error: any) {
      console.error('Error fetching admins:', error);
      alert('Failed to fetch admin list. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchAnnouncement = async () => {
    try {
      const res = await fetch('/api/site-settings/announcement');
      if (!res.ok) return;
      const data = await res.json();
      setAnnouncementEnabled(!!data.enabled);
      setAnnouncementContent(data.content || "");
    } catch {}
  };

  const fetchNotificationEmails = async () => {
    try {
      const res = await fetch('/api/site-settings/upload-notification-emails');
      if (!res.ok) return;
      const data = await res.json();
      setNotificationEmails(Array.isArray(data.emails) ? data.emails : []);
    } catch {}
  };

  const fetchApiKeys = async () => {
    if (!isCurrentUserSuperAdmin()) return;
    setIsLoadingApiKeys(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) return;
      const res = await fetch('/api/admin-management/api-keys', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to load API keys');
      const data = await res.json();
      setApiKeys(data || []);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingApiKeys(false);
    }
  };

  const handleCreateApiKey = async () => {
    if (!newApiKeyName.trim()) {
      alert('Enter a name for the API key (e.g., developer/team/application)');
      return;
    }
    setIsCreatingApiKey(true);
    try {
      const token = localStorage.getItem('jwt_token');
      const res = await fetch('/api/admin-management/api-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ name: newApiKeyName.trim(), scopes: newApiKeyScopes })
      });
      if (!res.ok) throw new Error('Failed to create API key');
      const created = await res.json();
      setJustCreatedKey(created);
      setNewApiKeyName("");
      await fetchApiKeys();
    } catch (e: any) {
      alert(e.message || 'Failed to create API key');
    } finally {
      setIsCreatingApiKey(false);
    }
  };

  const handleToggleScope = (scope: string) => {
    setNewApiKeyScopes(prev => prev.includes(scope) ? prev.filter(s => s !== scope) : [...prev, scope]);
  };

  const handleToggleActive = async (keyId: number, makeActive: boolean) => {
    try {
      const token = localStorage.getItem('jwt_token');
      const res = await fetch(`/api/admin-management/api-keys/${keyId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ is_active: makeActive })
      });
      if (!res.ok) throw new Error('Failed to update API key');
      await fetchApiKeys();
    } catch (e: any) {
      alert(e.message || 'Failed to update API key');
    }
  };

  const handleDeleteApiKey = async (keyId: number) => {
    if (!confirm('Delete this API key? This cannot be undone.')) return;
    try {
      const token = localStorage.getItem('jwt_token');
      const res = await fetch(`/api/admin-management/api-keys/${keyId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Failed to delete API key');
      await fetchApiKeys();
    } catch (e: any) {
      alert(e.message || 'Failed to delete API key');
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      alert('Copied to clipboard');
    } catch {}
  };

  // Add new admin (passwordless - uses OTP authentication)
  const handleAddAdmin = async () => {
    if (!newAdminEmail || !newAdminName) {
      alert('Please fill in email and name');
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
      setNewAdminRole('admin');
      await fetchAdmins();
      alert('Admin added successfully! They will use passwordless OTP login.');
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

  // Update admin role
  const handleUpdateAdminRole = async (adminId: number, adminEmail: string, makeSuper: boolean) => {
    if (adminEmail === currentUserEmail && !makeSuper) {
      alert('Cannot remove super admin privileges from your own account');
      return;
    }

    try {
      const token = localStorage.getItem('jwt_token');
      const response = await fetch(`/api/admin-management/admins/${adminId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          is_super_admin: makeSuper,
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update admin role');
      }

      await fetchAdmins();
      alert(`Admin ${makeSuper ? 'promoted to' : 'demoted from'} super admin successfully!`);
    } catch (error: any) {
      console.error('Error updating admin role:', error);
      alert(error.message || 'Failed to update admin role. Please try again.');
    }
  };


  useEffect(() => {
    fetchAdmins();
    fetchAnnouncement();
    fetchNotificationEmails();
    fetchApiKeys();
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
      {isCurrentUserSuperAdmin() && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Keys (Programmatic Access)
            </CardTitle>
            <CardDescription>
              Generate and manage API keys for developers. Keys can be scoped and disabled at any time.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2 space-y-2">
                <Label htmlFor="apiKeyName">Key Name</Label>
                <Input id="apiKeyName" value={newApiKeyName} onChange={e => setNewApiKeyName(e.target.value)} placeholder="e.g., Investigations Team" />
                <div className="mt-2">
                  <Label>Scopes</Label>
                  <div className="flex gap-3 mt-2 text-sm">
                    <button type="button" className={`px-3 py-1 rounded border ${newApiKeyScopes.includes('upload') ? 'bg-green-100 border-green-400' : 'bg-background'}`} onClick={() => handleToggleScope('upload')}>upload</button>
                    <button type="button" className={`px-3 py-1 rounded border ${newApiKeyScopes.includes('download') ? 'bg-green-100 border-green-400' : 'bg-background'}`} onClick={() => handleToggleScope('download')}>download</button>
                  </div>
                </div>
                <div className="mt-3">
                  <Button onClick={handleCreateApiKey} disabled={isCreatingApiKey}>
                    {isCreatingApiKey ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Plus className="h-4 w-4 mr-2" />}
                    Create API Key
                  </Button>
                </div>
                {justCreatedKey?.plaintext_key && (
                  <div className="p-3 mt-3 rounded border bg-muted">
                    <div className="text-sm font-medium">New API Key (shown once)</div>
                    <div className="mt-1 font-mono text-sm break-all">{justCreatedKey.plaintext_key}</div>
                    <div className="mt-2 flex gap-2">
                      <Button size="sm" variant="outline" onClick={() => copyToClipboard(justCreatedKey.plaintext_key!)}>
                        <Copy className="h-4 w-4 mr-2" /> Copy
                      </Button>
                    </div>
                  </div>
                )}
              </div>
              <div className="md:col-span-1 text-sm text-muted-foreground">
                <div className="font-medium">Usage</div>
                <pre className="mt-2 p-2 rounded bg-muted text-xs whitespace-pre-wrap">{`# Upload (multipart)
curl -X POST \
  -H "X-API-Key: <your_key>" \
  -F file=@/path/doc.pdf \
  -F title="Title" -F country="BR" -F state="SP" \
  https://www.haqnow.com/api/file-uploader/upload

# Download PDF
curl -H "X-API-Key: <your_key>" \
  https://www.haqnow.com/api/search/download/123`}</pre>
              </div>
            </div>

            <div className="mt-6">
              <div className="flex items-center justify-between mb-2">
                <div className="font-medium">Existing Keys</div>
                {isLoadingApiKeys && <Loader2 className="h-4 w-4 animate-spin" />}
              </div>
              <div className="space-y-2">
                {apiKeys.map(k => (
                  <div key={k.id} className="flex items-center justify-between p-3 border rounded">
                    <div className="min-w-0">
                      <div className="font-medium truncate">{k.name} <span className="text-xs text-muted-foreground">(prefix: {k.key_prefix})</span></div>
                      <div className="text-xs text-muted-foreground mt-1">scopes: {k.scopes.join(', ') || '—'} • created {new Date(k.created_at).toLocaleString()} • used {k.usage_count}×</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button size="sm" variant="outline" onClick={() => handleToggleActive(k.id, !k.is_active)} title={k.is_active ? 'Disable' : 'Enable'}>
                        {k.is_active ? <ToggleRight className="h-4 w-4" /> : <ToggleLeft className="h-4 w-4" />}
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="outline" title="Delete">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Delete API Key</AlertDialogTitle>
                            <AlertDialogDescription>This cannot be undone. Applications using this key will stop working.</AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleDeleteApiKey(k.id)}>Delete</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </div>
                ))}
                {apiKeys.length === 0 && !isLoadingApiKeys && (
                  <div className="text-sm text-muted-foreground">No API keys yet.</div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
      {isCurrentUserSuperAdmin() && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Megaphone className="h-5 w-5" />
              Upload Notification Emails
            </CardTitle>
            <CardDescription>
              Configure recipients who are emailed whenever a new document is uploaded
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                placeholder="user@example.com"
                value={newNotificationEmail}
                onChange={(e) => setNewNotificationEmail(e.target.value)}
              />
              <Button
                onClick={() => {
                  const email = newNotificationEmail.trim();
                  if (!email) return;
                  if (notificationEmails.includes(email)) return;
                  setNotificationEmails(prev => [...prev, email]);
                  setNewNotificationEmail("");
                }}
              >Add</Button>
            </div>
            <div className="space-y-2">
              {notificationEmails.length === 0 && (
                <div className="text-sm text-muted-foreground">No recipients configured.</div>
              )}
              {notificationEmails.map((e) => (
                <div key={e} className="flex items-center justify-between p-2 border rounded">
                  <div className="text-sm">{e}</div>
                  <Button size="sm" variant="outline" onClick={() => setNotificationEmails(prev => prev.filter(x => x !== e))}>Remove</Button>
                </div>
              ))}
            </div>
            <div>
              <Button
                onClick={async () => {
                  try {
                    const token = localStorage.getItem('jwt_token');
                    const res = await fetch('/api/site-settings/upload-notification-emails', {
                      method: 'PUT',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                      },
                      body: JSON.stringify({ emails: notificationEmails }),
                    });
                    if (!res.ok) throw new Error('Failed to save');
                    alert('Notification recipients saved');
                  } catch (e: any) {
                    alert(e.message || 'Failed to save recipients');
                  }
                }}
              >Save Recipients</Button>
            </div>
          </CardContent>
        </Card>
      )}
      {/* Announcement Banner Management */}
      {isCurrentUserSuperAdmin() && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Megaphone className="h-5 w-5" />
              Site Announcement Banner
            </CardTitle>
            <CardDescription>
              Show a global announcement banner on all pages
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={announcementEnabled}
                  onChange={(e) => setAnnouncementEnabled(e.target.checked)}
                />
                Enable banner
              </label>
            </div>
            <div>
              <Label htmlFor="announcementContent">Banner Content (HTML allowed)</Label>
              <textarea
                id="announcementContent"
                className="mt-1 w-full min-h-[120px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                placeholder="e.g., <strong>Maintenance:</strong> Site will be read-only on Friday 10:00–12:00 UTC."
                value={announcementContent}
                onChange={(e) => setAnnouncementContent(e.target.value)}
              />
              <p className="text-xs text-muted-foreground mt-1">You can use simple HTML for formatting. Avoid scripts.</p>
            </div>
            <div>
              <Button
                onClick={async () => {
                  setIsSavingAnnouncement(true);
                  try {
                    const token = localStorage.getItem('jwt_token');
                    const res = await fetch('/api/site-settings/announcement', {
                      method: 'PUT',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                      },
                      body: JSON.stringify({ enabled: announcementEnabled, content: announcementContent }),
                    });
                    if (!res.ok) throw new Error('Failed to save');
                    alert('Announcement updated');
                  } catch (e: any) {
                    alert(e.message || 'Failed to save announcement');
                  } finally {
                    setIsSavingAnnouncement(false);
                  }
                }}
                disabled={isSavingAnnouncement}
              >
                {isSavingAnnouncement ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
                Save Banner
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-primary font-serif">Admin Management</h1>
          <p className="text-muted-foreground">Manage administrator accounts and security settings</p>
        </div>
      </div>


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
              <p className="text-xs text-muted-foreground mt-1">
                New admins will use passwordless OTP login via email
              </p>
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

      {/* Current Administrators List - Only for Super Admins */}
      {isCurrentUserSuperAdmin() && (
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
                  </div>
                  <p className="text-sm text-muted-foreground">{admin.email}</p>
                  <p className="text-xs text-muted-foreground">
                    Created: {new Date(admin.created_at).toLocaleDateString()}
                    {admin.last_login_at && (
                      <> • Last login: {new Date(admin.last_login_at).toLocaleDateString()}</>
                    )}
                  </p>
                </div>
                {isCurrentUserSuperAdmin() && (
                  <div className="flex gap-2">
                    {/* Role Management Buttons */}
                    {admin.email !== currentUserEmail && (
                      <>
                        {!admin.is_super_admin ? (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="outline" size="sm" title="Promote to Super Admin">
                                <Shield className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Promote to Super Admin</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to promote "{admin.name}" to Super Admin? 
                                  They will have full administrative privileges.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction 
                                  onClick={() => handleUpdateAdminRole(admin.id, admin.email, true)}
                                >
                                  Promote
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        ) : (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button variant="outline" size="sm" title="Demote from Super Admin">
                                <ShieldCheck className="h-4 w-4" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Demote from Super Admin</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to demote "{admin.name}" from Super Admin? 
                                  They will lose administrative privileges.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction 
                                  onClick={() => handleUpdateAdminRole(admin.id, admin.email, false)}
                                  className="bg-orange-600 text-white hover:bg-orange-700"
                                >
                                  Demote
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                        
                        {/* Delete Button */}
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button variant="outline" size="sm" title="Delete Admin">
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
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      )}

    </div>
  );
} 