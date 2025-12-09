import React, { useState, useEffect } from "react";
import { Link, useNavigate, Outlet, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { 
  DndContext, 
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { LayoutDashboard, FileCheck, FileText, Tag, Users, Settings, LogOut, ShieldBan, Loader2, Languages, TrendingUp, MessageSquare, BarChart3, Plus, Edit, Trash2, ExternalLink, GripVertical } from "lucide-react";

// Logout function
const handleLogout = (navigate: Function) => {
  console.log("Admin logged out");
  // Clear JWT token and user data
  localStorage.removeItem('jwt_token');
  localStorage.removeItem('user_email');
  navigate("/admin-login-page");
};

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  isExternal?: boolean;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label, isExternal }) => (
  <Button asChild variant="ghost" className="w-full justify-start text-base py-6">
    {isExternal ? (
      <a href={to} target="_blank" rel="noopener noreferrer">
        {icon}
        {label}
      </a>
    ) : (
      <Link to={to}>
        {icon}
        {label}
      </Link>
    )}
  </Button>
);

// Sortable Collaborator Item Component
interface SortableCollaboratorItemProps {
  collaborator: Collaborator;
  onEdit: (collaborator: Collaborator) => void;
  onDelete: (id: number) => void;
}

function SortableCollaboratorItem({ collaborator, onEdit, onDelete }: SortableCollaboratorItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: collaborator.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 ${
        isDragging ? 'bg-muted shadow-lg' : ''
      }`}
    >
      <div className="flex items-center gap-4 flex-1">
        {/* Drag Handle */}
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing text-muted-foreground hover:text-foreground p-2 -ml-2"
        >
          <GripVertical className="h-5 w-5" />
        </div>
        
        <img
          src={collaborator.logo_url}
          alt={collaborator.name}
          className="h-16 w-32 object-contain"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold">{collaborator.name}</h3>
            {!collaborator.is_active && (
              <Badge variant="secondary">Inactive</Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-1">
            {collaborator.description}
          </p>
          <a
            href={collaborator.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-blue-600 hover:underline flex items-center gap-1 mt-1"
          >
            {collaborator.website_url}
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => onEdit(collaborator)}
        >
          <Edit className="h-4 w-4" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => onDelete(collaborator.id)}
        >
          <Trash2 className="h-4 w-4 text-destructive" />
        </Button>
      </div>
    </div>
  );
}

interface Collaborator {
  id: number;
  name: string;
  description: string;
  logo_url: string;
  logo_path: string;
  website_url: string;
  display_order: number;
  is_active: boolean;
  created_by: string | null;
  created_at: string;
  updated_at: string;
}

export default function AdminDashboardPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // State for dashboard statistics
  const [pendingCount, setPendingCount] = useState<number | null>(null);
  const [bannedTagsCount, setBannedTagsCount] = useState<number | null>(null);
  const [isLoadingPending, setIsLoadingPending] = useState(true);
  const [isLoadingBanned, setIsLoadingBanned] = useState(true);
  
  // Collaborators state
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [isLoadingCollaborators, setIsLoadingCollaborators] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingCollaborator, setEditingCollaborator] = useState<Collaborator | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  
  // Form state
  const [formName, setFormName] = useState("");
  const [formDescription, setFormDescription] = useState("");
  const [formWebsiteUrl, setFormWebsiteUrl] = useState("");
  const [formIsActive, setFormIsActive] = useState(true);
  const [formLogo, setFormLogo] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isReordering, setIsReordering] = useState(false);
  
  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Fetch pending documents count
  const fetchPendingCount = async () => {
    setIsLoadingPending(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        console.error('No authentication token found');
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/document-processing/documents?status=pending&per_page=1', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.error('Authentication failed');
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setPendingCount(data.total_count || 0);
    } catch (error: any) {
      console.error('Error fetching pending documents count:', error);
      setPendingCount(0);
    } finally {
      setIsLoadingPending(false);
    }
  };

  // Fetch banned tags count
  const fetchBannedTagsCount = async () => {
    setIsLoadingBanned(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        console.error('No authentication token found');
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/search/banned-tags', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.error('Authentication failed');
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setBannedTagsCount(data.count || 0);
    } catch (error: any) {
      console.error('Error fetching banned tags count:', error);
      setBannedTagsCount(0);
    } finally {
      setIsLoadingBanned(false);
    }
  };

  // Fetch collaborators
  const fetchCollaborators = async () => {
    setIsLoadingCollaborators(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/collaborators/all', {
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
      setCollaborators(data.collaborators || []);
    } catch (error: any) {
      console.error('Error fetching collaborators:', error);
    } finally {
      setIsLoadingCollaborators(false);
    }
  };

  // Fetch data on component mount
  useEffect(() => {
    fetchPendingCount();
    fetchBannedTagsCount();
    fetchCollaborators();
  }, []);

  // Handle logo file selection
  const handleLogoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setFormLogo(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  // Reset form
  const resetForm = () => {
    setFormName("");
    setFormDescription("");
    setFormWebsiteUrl("");
    setFormIsActive(true);
    setFormLogo(null);
    setLogoPreview(null);
    setEditingCollaborator(null);
  };

  // Open add dialog
  const handleAddClick = () => {
    resetForm();
    setIsDialogOpen(true);
  };

  // Open edit dialog
  const handleEditClick = (collaborator: Collaborator) => {
    setFormName(collaborator.name);
    setFormDescription(collaborator.description);
    setFormWebsiteUrl(collaborator.website_url);
    setFormIsActive(collaborator.is_active);
    setLogoPreview(collaborator.logo_url);
    setEditingCollaborator(collaborator);
    setIsDialogOpen(true);
  };

  // Save collaborator
  const handleSave = async () => {
    if (!formName || !formDescription || !formWebsiteUrl) {
      alert("Please fill in all required fields");
      return;
    }

    setIsSaving(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const formData = new FormData();
      formData.append('name', formName);
      formData.append('description', formDescription);
      formData.append('website_url', formWebsiteUrl);
      formData.append('is_active', formIsActive.toString());
      
      if (formLogo) {
        formData.append('logo', formLogo);
      }

      const url = editingCollaborator 
        ? `/api/collaborators/${editingCollaborator.id}`
        : '/api/collaborators';
      const method = editingCollaborator ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save collaborator');
      }

      setIsDialogOpen(false);
      resetForm();
      fetchCollaborators();
    } catch (error: any) {
      console.error('Error saving collaborator:', error);
      alert(error.message || 'Failed to save collaborator');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle drag end
  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) {
      return;
    }

    const oldIndex = collaborators.findIndex((c) => c.id === active.id);
    const newIndex = collaborators.findIndex((c) => c.id === over.id);

    if (oldIndex === -1 || newIndex === -1) {
      return;
    }

    // Optimistically update UI
    const newCollaborators = arrayMove(collaborators, oldIndex, newIndex);
    setCollaborators(newCollaborators);

    // Update backend
    setIsReordering(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const collaboratorIds = newCollaborators.map((c) => c.id);

      const response = await fetch('/api/collaborators/reorder', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ collaborator_ids: collaboratorIds }),
      });

      if (!response.ok) {
        throw new Error('Failed to reorder collaborators');
      }

      // Refresh to get updated data
      fetchCollaborators();
    } catch (error: any) {
      console.error('Error reordering collaborators:', error);
      // Revert on error
      fetchCollaborators();
      alert('Failed to reorder collaborators');
    } finally {
      setIsReordering(false);
    }
  };

  // Delete collaborator
  const handleDelete = async () => {
    if (!deletingId) return;

    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch(`/api/collaborators/${deletingId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete collaborator');
      }

      setDeleteDialogOpen(false);
      setDeletingId(null);
      fetchCollaborators();
    } catch (error: any) {
      console.error('Error deleting collaborator:', error);
      alert('Failed to delete collaborator');
    }
  };

  // This component will act as a layout for other admin sub-pages using <Outlet />
  // For now, it will display a welcome message and links to future admin sections.

  return (
    <div className="min-h-screen flex bg-muted/40">
      {/* Sidebar Navigation */}
      <aside className="w-64 bg-background border-r border-border p-6 flex flex-col justify-between shadow-lg">
        <div>
          <div className="mb-8 text-center">
            <Link to="/admin-dashboard-page" className="text-2xl font-bold text-primary font-serif">
              Admin Panel
            </Link>
            <p className="text-sm text-muted-foreground">Dig Out the Dirt</p>
          </div>
          <nav className="space-y-2">
            <NavItem to="/admin-dashboard-page" icon={<LayoutDashboard className="mr-3 h-5 w-5" />} label="Dashboard Home" />
            <NavItem to="/admin-analytics-page" icon={<BarChart3 className="mr-3 h-5 w-5" />} label="Analytics" />
            <NavItem to="/admin-pending-documents-page" icon={<FileCheck className="mr-3 h-5 w-5" />} label="Pending Documents" />
            <NavItem to="/admin-approved-documents-page" icon={<FileText className="mr-3 h-5 w-5" />} label="Approved Documents" />
            <NavItem to="/admin-banned-tags-page" icon={<ShieldBan className="mr-3 h-5 w-5" />} label="Manage Banned Tags" />
            <NavItem to="/admin-banned-words-page" icon={<ShieldBan className="mr-3 h-5 w-5" />} label="Manage Banned Words" />
            <NavItem to="/admin-comment-moderation-page" icon={<MessageSquare className="mr-3 h-5 w-5" />} label="Comment Moderation" />
            <NavItem to="/admin-translations-page" icon={<Languages className="mr-3 h-5 w-5" />} label="Manage Translations" />
            <NavItem to="/admin-top-viewed-page" icon={<TrendingUp className="mr-3 h-5 w-5" />} label="Top Viewed Documents" />
            <NavItem to="/admin-management-page" icon={<Users className="mr-3 h-5 w-5" />} label="Admin Management" />
            {/* <NavItem to="/admin/settings" icon={<Settings className="mr-3 h-5 w-5" />} label="Settings" /> */}
          </nav>
        </div>
        <Button variant="outline" onClick={() => handleLogout(navigate)} className="w-full mt-auto">
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </Button>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-10 overflow-auto">
        {/* Outlet will render the content of nested routes (e.g., AdminPendingDocumentsPage) */}
        {/* For the /admin/dashboard route itself, we can show a welcome or overview */}
        {location.pathname === "/admin-dashboard-page" || location.pathname === "/admin-dashboard-page/" ? (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-3xl font-serif">Welcome, Administrator!</CardTitle>
                <CardDescription>Select an option from the sidebar to manage the platform.</CardDescription>
              </CardHeader>
              <CardContent>
                <p>This is the main dashboard area. Future updates will include statistics and quick actions here.</p>
                <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Link to="/admin-pending-documents-page">
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-card/50 hover:bg-card">
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">PENDING DOCUMENTS</CardTitle>
                        <FileCheck className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold flex items-center">
                          {isLoadingPending ? (
                            <Loader2 className="h-6 w-6 animate-spin" />
                          ) : (
                            pendingCount
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          documents awaiting review
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                  <Link to="/admin-banned-tags-page">
                    <Card className="hover:shadow-lg transition-shadow cursor-pointer bg-card/50 hover:bg-card">
                      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">BANNED TAGS</CardTitle>
                        <ShieldBan className="h-4 w-4 text-muted-foreground" />
                      </CardHeader>
                      <CardContent>
                        <div className="text-2xl font-bold flex items-center">
                          {isLoadingBanned ? (
                            <Loader2 className="h-6 w-6 animate-spin" />
                          ) : (
                            bannedTagsCount
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground">
                          tags currently banned
                        </p>
                      </CardContent>
                    </Card>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Collaborators & Champions Management */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Collaborators & Champions</CardTitle>
                    <CardDescription>Manage partner logos and descriptions</CardDescription>
                  </div>
                  <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                    <DialogTrigger asChild>
                      <Button onClick={handleAddClick}>
                        <Plus className="h-4 w-4 mr-2" />
                        Add Collaborator
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                      <DialogHeader>
                        <DialogTitle>
                          {editingCollaborator ? 'Edit Collaborator' : 'Add New Collaborator'}
                        </DialogTitle>
                        <DialogDescription>
                          Add or update a collaborator/champion. Logo will be displayed on homepage and about page.
                        </DialogDescription>
                      </DialogHeader>
                      <div className="space-y-4 py-4">
                        <div className="space-y-2">
                          <Label htmlFor="name">Name *</Label>
                          <Input
                            id="name"
                            value={formName}
                            onChange={(e) => setFormName(e.target.value)}
                            placeholder="Organization name"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="description">Description *</Label>
                          <Textarea
                            id="description"
                            value={formDescription}
                            onChange={(e) => setFormDescription(e.target.value)}
                            placeholder="One sentence description"
                            rows={3}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="website_url">Website URL *</Label>
                          <Input
                            id="website_url"
                            value={formWebsiteUrl}
                            onChange={(e) => setFormWebsiteUrl(e.target.value)}
                            placeholder="https://example.com"
                            type="url"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="logo">Logo {editingCollaborator && !formLogo ? '(optional)' : '*'}</Label>
                          <Input
                            id="logo"
                            type="file"
                            accept="image/png,image/jpeg,image/svg+xml,image/webp"
                            onChange={handleLogoChange}
                          />
                          {logoPreview && (
                            <div className="mt-2">
                              <img
                                src={logoPreview}
                                alt="Logo preview"
                                className="max-h-32 max-w-full object-contain border rounded"
                              />
                            </div>
                          )}
                          <p className="text-xs text-muted-foreground">
                            PNG, JPG, SVG, or WebP. Max 2MB.
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="is_active"
                            checked={formIsActive}
                            onChange={(e) => setFormIsActive(e.target.checked)}
                            className="rounded"
                          />
                          <Label htmlFor="is_active">Active (visible on site)</Label>
                        </div>
                      </div>
                      <DialogFooter>
                        <Button variant="outline" onClick={() => setIsDialogOpen(false)}>
                          Cancel
                        </Button>
                        <Button onClick={handleSave} disabled={isSaving}>
                          {isSaving ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Saving...
                            </>
                          ) : (
                            'Save'
                          )}
                        </Button>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </div>
              </CardHeader>
              <CardContent>
                {isLoadingCollaborators ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : collaborators.length === 0 ? (
                  <p className="text-muted-foreground text-center py-8">
                    No collaborators yet. Click "Add Collaborator" to get started.
                  </p>
                ) : (
                  <DndContext
                    sensors={sensors}
                    collisionDetection={closestCenter}
                    onDragEnd={handleDragEnd}
                  >
                    <SortableContext
                      items={collaborators.map((c) => c.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      <div className="space-y-4">
                        {collaborators.map((collaborator) => (
                          <SortableCollaboratorItem
                            key={collaborator.id}
                            collaborator={collaborator}
                            onEdit={handleEditClick}
                            onDelete={(id) => {
                              setDeletingId(id);
                              setDeleteDialogOpen(true);
                            }}
                          />
                        ))}
                      </div>
                    </SortableContext>
                    {isReordering && (
                      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                        <div className="bg-white p-4 rounded-lg">
                          <Loader2 className="h-6 w-6 animate-spin mx-auto" />
                          <p className="mt-2 text-sm">Reordering...</p>
                        </div>
                      </div>
                    )}
                  </DndContext>
                )}
              </CardContent>
            </Card>

            <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Collaborator?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will remove the collaborator from the site. The logo will also be deleted from storage.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel onClick={() => setDeletingId(null)}>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground">
                    Delete
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        ) : (
          <Outlet />
        )}
      </main>
    </div>
  );
}
