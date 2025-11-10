import { Moon, Sun, LogOut } from "lucide-react";
import { Button } from "./ui/button";

interface HeaderProps {
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
  onLogout: () => void;
}

export function Header({ isDarkMode, onToggleDarkMode, onLogout }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-blue-600 to-blue-500 shadow-md">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
              <span className="text-blue-600">AI</span>
            </div>
            <div>
              <h1 className="text-white">AI-CLAIM Lite</h1>
              <p className="text-blue-100 text-xs">Admin Meta Dashboard</p>
            </div>
          </div>

          {/* Right Actions */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:block text-white text-sm">
              Admin Meta
            </div>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={onToggleDarkMode}
              className="text-white hover:bg-blue-700"
            >
              {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={onLogout}
              className="text-red-300 hover:bg-red-600 hover:text-white"
            >
              <LogOut className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}
