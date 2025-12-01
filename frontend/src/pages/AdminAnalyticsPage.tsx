import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  LayoutDashboard, FileCheck, FileText, Tag, Users, LogOut, ShieldBan, 
  Loader2, Languages, TrendingUp, MessageSquare, BarChart3, Upload, 
  Eye, Clock, Globe, FileType, RefreshCw, ExternalLink
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend
} from "recharts";

// Logout function
const handleLogout = (navigate: Function) => {
  localStorage.removeItem('jwt_token');
  localStorage.removeItem('user_email');
  navigate("/admin-login-page");
};

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const NavItem: React.FC<NavItemProps> = ({ to, icon, label }) => (
  <Button asChild variant="ghost" className="w-full justify-start text-base py-6">
    <Link to={to}>
      {icon}
      {label}
    </Link>
  </Button>
);

// Analytics data types
interface TimeSeriesDataPoint {
  date: string;
  count: number;
}

interface UploadStats {
  total_uploads: number;
  uploads_today: number;
  uploads_this_week: number;
  uploads_this_month: number;
  uploads_by_day: TimeSeriesDataPoint[];
  uploads_by_week: TimeSeriesDataPoint[];
  uploads_by_month: TimeSeriesDataPoint[];
}

interface DocumentStatusStats {
  total_documents: number;
  pending: number;
  approved: number;
  rejected: number;
  processed: number;
}

interface EngagementStats {
  total_views: number;
  total_comments: number;
  comments_pending: number;
  comments_approved: number;
  total_rag_queries: number;
  avg_rag_response_time_ms: number | null;
}

interface CountryUploadStat {
  country: string;
  count: number;
}

interface LanguageUploadStat {
  language: string;
  count: number;
}

interface ProcessingStats {
  jobs_pending: number;
  jobs_processing: number;
  jobs_completed: number;
  jobs_failed: number;
  avg_processing_time_seconds: number | null;
}

interface AnalyticsSummary {
  upload_stats: UploadStats;
  document_status: DocumentStatusStats;
  engagement: EngagementStats;
  uploads_by_country: CountryUploadStat[];
  uploads_by_language: LanguageUploadStat[];
  processing_stats: ProcessingStats;
  generated_at: string;
}

// Color palette for charts
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];
const STATUS_COLORS = {
  approved: '#10b981',
  pending: '#f59e0b',
  rejected: '#ef4444',
  processed: '#3b82f6'
};

export default function AdminAnalyticsPage() {
  const navigate = useNavigate();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/analytics/summary', {
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
      setAnalytics(data);
      setLastRefresh(new Date());
    } catch (err: any) {
      console.error('Error fetching analytics:', err);
      setError(err.message || 'Failed to load analytics');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAnalytics, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Format date for display
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  // Format yearweek to readable format
  const formatYearWeek = (yearweek: string) => {
    const year = yearweek.substring(0, 4);
    const week = yearweek.substring(4);
    return `W${week}`;
  };

  // Prepare chart data
  const prepareUploadsChartData = () => {
    if (!analytics) return [];
    return analytics.upload_stats.uploads_by_day.map(item => ({
      date: formatDate(item.date),
      uploads: item.count
    }));
  };

  const prepareStatusChartData = () => {
    if (!analytics) return [];
    return [
      { name: 'Approved', value: analytics.document_status.approved, color: STATUS_COLORS.approved },
      { name: 'Pending', value: analytics.document_status.pending, color: STATUS_COLORS.pending },
      { name: 'Rejected', value: analytics.document_status.rejected, color: STATUS_COLORS.rejected },
    ].filter(item => item.value > 0);
  };

  const prepareCountryChartData = () => {
    if (!analytics) return [];
    return analytics.uploads_by_country.slice(0, 10).map(item => ({
      country: item.country.length > 15 ? item.country.substring(0, 12) + '...' : item.country,
      uploads: item.count
    }));
  };

  const prepareLanguageChartData = () => {
    if (!analytics) return [];
    return analytics.uploads_by_language.map(item => ({
      name: item.language.charAt(0).toUpperCase() + item.language.slice(1),
      value: item.count
    }));
  };

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
          </nav>
        </div>
        <Button variant="outline" onClick={() => handleLogout(navigate)} className="w-full mt-auto">
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </Button>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 p-6 md:p-10 overflow-auto">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="flex justify-between items-center mb-8">
            <div>
              <h1 className="text-3xl font-bold font-serif">Analytics Dashboard</h1>
              <p className="text-muted-foreground mt-1">
                Platform metrics and upload statistics
              </p>
            </div>
            <div className="flex items-center gap-4">
              {lastRefresh && (
                <span className="text-sm text-muted-foreground">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </span>
              )}
              <Button 
                variant="outline" 
                onClick={fetchAnalytics}
                disabled={isLoading}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button variant="outline" asChild>
                <a href="https://www.haqnow.com/monitoring" target="_blank" rel="noopener noreferrer">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Visitor Analytics
                </a>
              </Button>
            </div>
          </div>

          {error && (
            <Card className="mb-6 border-red-500 bg-red-50 dark:bg-red-950">
              <CardContent className="pt-6">
                <p className="text-red-600 dark:text-red-400">{error}</p>
              </CardContent>
            </Card>
          )}

          {isLoading && !analytics ? (
            <div className="flex items-center justify-center h-64">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : analytics && (
            <>
              {/* Quick Stats Row */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-600/5 border-emerald-500/20">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Uploads</CardTitle>
                    <Upload className="h-4 w-4 text-emerald-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.upload_stats.total_uploads.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      +{analytics.upload_stats.uploads_this_month} this month
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Views</CardTitle>
                    <Eye className="h-4 w-4 text-blue-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.engagement.total_views.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      {analytics.engagement.total_comments} comments
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Pending Review</CardTitle>
                    <Clock className="h-4 w-4 text-amber-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.document_status.pending}</div>
                    <p className="text-xs text-muted-foreground">
                      {analytics.engagement.comments_pending} comments pending
                    </p>
                  </CardContent>
                </Card>

                <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">AI Queries</CardTitle>
                    <BarChart3 className="h-4 w-4 text-purple-600" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.engagement.total_rag_queries.toLocaleString()}</div>
                    <p className="text-xs text-muted-foreground">
                      {analytics.engagement.avg_rag_response_time_ms 
                        ? `${(analytics.engagement.avg_rag_response_time_ms / 1000).toFixed(1)}s avg response`
                        : 'No response data'}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Charts Row 1 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Uploads Over Time */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TrendingUp className="h-5 w-5" />
                      Uploads Over Time (30 days)
                    </CardTitle>
                    <CardDescription>Daily document uploads</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={prepareUploadsChartData()}>
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis 
                            dataKey="date" 
                            tick={{ fontSize: 12 }}
                            className="text-muted-foreground"
                          />
                          <YAxis 
                            tick={{ fontSize: 12 }}
                            className="text-muted-foreground"
                          />
                          <Tooltip 
                            contentStyle={{ 
                              backgroundColor: 'hsl(var(--background))',
                              border: '1px solid hsl(var(--border))',
                              borderRadius: '8px'
                            }}
                          />
                          <Line 
                            type="monotone" 
                            dataKey="uploads" 
                            stroke="#10b981" 
                            strokeWidth={2}
                            dot={{ fill: '#10b981', strokeWidth: 2 }}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Document Status Distribution */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Document Status
                    </CardTitle>
                    <CardDescription>Current status distribution</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={prepareStatusChartData()}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={100}
                            paddingAngle={5}
                            dataKey="value"
                            label={({ name, value }) => `${name}: ${value}`}
                          >
                            {prepareStatusChartData().map((entry, index) => (
                              <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Charts Row 2 */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Uploads by Country */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Globe className="h-5 w-5" />
                      Top Countries by Uploads
                    </CardTitle>
                    <CardDescription>Document source countries</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={prepareCountryChartData()} layout="vertical">
                          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                          <XAxis type="number" tick={{ fontSize: 12 }} />
                          <YAxis 
                            dataKey="country" 
                            type="category" 
                            width={100}
                            tick={{ fontSize: 11 }}
                          />
                          <Tooltip />
                          <Bar dataKey="uploads" fill="#3b82f6" radius={[0, 4, 4, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>

                {/* Uploads by Language */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileType className="h-5 w-5" />
                      Document Languages
                    </CardTitle>
                    <CardDescription>Language distribution of uploads</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="h-[300px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={prepareLanguageChartData()}
                            cx="50%"
                            cy="50%"
                            outerRadius={100}
                            dataKey="value"
                            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                          >
                            {prepareLanguageChartData().map((_, index) => (
                              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                          </Pie>
                          <Tooltip />
                          <Legend />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Processing Stats */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Document Processing Queue
                  </CardTitle>
                  <CardDescription>Background job statistics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-amber-600">
                        {analytics.processing_stats.jobs_pending}
                      </div>
                      <p className="text-sm text-muted-foreground">Pending</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-blue-600">
                        {analytics.processing_stats.jobs_processing}
                      </div>
                      <p className="text-sm text-muted-foreground">Processing</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-emerald-600">
                        {analytics.processing_stats.jobs_completed}
                      </div>
                      <p className="text-sm text-muted-foreground">Completed</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-red-600">
                        {analytics.processing_stats.jobs_failed}
                      </div>
                      <p className="text-sm text-muted-foreground">Failed</p>
                    </div>
                    <div className="text-center p-4 bg-muted/50 rounded-lg">
                      <div className="text-2xl font-bold text-purple-600">
                        {analytics.processing_stats.avg_processing_time_seconds 
                          ? `${analytics.processing_stats.avg_processing_time_seconds.toFixed(0)}s`
                          : 'N/A'}
                      </div>
                      <p className="text-sm text-muted-foreground">Avg Time</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      </main>
    </div>
  );
}

