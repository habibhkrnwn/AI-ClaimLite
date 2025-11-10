import { Users, UserCheck, FileText, Calendar, TrendingUp } from "lucide-react";
import { Card, CardContent } from "./ui/card";

interface MetricCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  colorClass: string;
}

function MetricCard({ title, value, icon, colorClass }: MetricCardProps) {
  return (
    <Card className={`${colorClass} border-none shadow-md`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-2">{title}</p>
            <p className="text-3xl">{value}</p>
          </div>
          <div className="opacity-60">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function SummaryCards() {
  return (
    <div className="mb-8">
      <h2 className="text-blue-900 mb-6">Admin Meta Dashboard</h2>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        <MetricCard
          title="Total Users"
          value="48"
          icon={<Users className="h-8 w-8" />}
          colorClass="bg-blue-50 text-blue-900"
        />
        <MetricCard
          title="Active Users"
          value="42"
          icon={<UserCheck className="h-8 w-8" />}
          colorClass="bg-green-50 text-green-900"
        />
        <MetricCard
          title="Total Analyses"
          value="1,247"
          icon={<FileText className="h-8 w-8" />}
          colorClass="bg-purple-50 text-purple-900"
        />
        <MetricCard
          title="Today"
          value="23"
          icon={<Calendar className="h-8 w-8" />}
          colorClass="bg-orange-50 text-orange-900"
        />
        <MetricCard
          title="This Week"
          value="156"
          icon={<TrendingUp className="h-8 w-8" />}
          colorClass="bg-pink-50 text-pink-900"
        />
      </div>
    </div>
  );
}
