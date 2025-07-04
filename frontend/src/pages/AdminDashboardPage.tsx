import React from "react";
import { Link, useNavigate, Outlet } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { LayoutDashboard, FileCheck, FileText, Tag, Users, Settings, LogOut, ShieldBan } from "lucide-react";

// Mock function for logout
const handleLogout = (navigate: Function) => {
  console.log("Admin logged out (mock)");
  // In a real app, clear auth state
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

export default function AdminDashboardPage() {
  const navigate = useNavigate();

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
            <NavItem to="/admin-pending-documents-page" icon={<FileCheck className="mr-3 h-5 w-5" />} label="Pending Documents" />
            {/* <NavItem to="/admin/approved-documents" icon={<FileText className="mr-3 h-5 w-5" />} label="Approved Documents" /> */}
            <NavItem to="/admin-banned-tags-page" icon={<ShieldBan className="mr-3 h-5 w-5" />} label="Manage Banned Tags" />
            {/* <NavItem to="/admin/users" icon={<Users className="mr-3 h-5 w-5" />} label="User Management" /> */}
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
                      <div className="text-2xl font-bold">15</div> {/* Mock count */}
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
                      <div className="text-2xl font-bold">5</div> {/* Mock count */}
                      <p className="text-xs text-muted-foreground">
                        tags currently banned
                      </p>
                    </CardContent>
                  </Card>
                </Link>
              </div>
            </CardContent>
          </Card>
        ) : (
          <Outlet />
        )}
      </main>
    </div>
  );
}
