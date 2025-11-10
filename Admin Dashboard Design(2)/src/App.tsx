import { useState } from "react";
import { Header } from "./components/Header";
import { SummaryCards } from "./components/SummaryCards";
import { UserManagementTable } from "./components/UserManagementTable";
import { UsageStatisticsTable } from "./components/UsageStatisticsTable";
import { CreateAdminDialog } from "./components/CreateAdminDialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Toaster } from "./components/ui/sonner";
import { toast } from "sonner@2.0.3";

export default function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);

  const handleToggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    toast.info(isDarkMode ? "Light mode activated" : "Dark mode activated");
  };

  const handleLogout = () => {
    toast.success("Logged out successfully");
  };

  return (
    <div className={isDarkMode ? "dark bg-gray-900 min-h-screen" : "bg-gray-50 min-h-screen"}>
      <Header
        isDarkMode={isDarkMode}
        onToggleDarkMode={handleToggleDarkMode}
        onLogout={handleLogout}
      />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 pt-24 pb-12">
        <SummaryCards />

        <div className="flex justify-between items-center mb-6">
          <div></div>
          <CreateAdminDialog />
        </div>

        <Tabs defaultValue="users" className="w-full">
          <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
            <TabsTrigger
              value="users"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              User Management
            </TabsTrigger>
            <TabsTrigger
              value="statistics"
              className="data-[state=active]:bg-blue-600 data-[state=active]:text-white"
            >
              Usage Statistics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="users" className="mt-0">
            <UserManagementTable />
          </TabsContent>

          <TabsContent value="statistics" className="mt-0">
            <UsageStatisticsTable />
          </TabsContent>
        </Tabs>
      </main>

      <Toaster />
    </div>
  );
}
