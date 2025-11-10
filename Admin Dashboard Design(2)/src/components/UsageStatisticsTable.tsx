import { Badge } from "./ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";

interface UsageStats {
  id: string;
  fullName: string;
  email: string;
  status: "Active" | "Inactive";
  totalAnalyses: number;
  lastAnalysis: string;
}

const mockStats: UsageStats[] = [
  {
    id: "1",
    fullName: "RSUD Jakarta Pusat",
    email: "admin.rsudjakarta@hospital.id",
    status: "Active",
    totalAnalyses: 342,
    lastAnalysis: "2025-11-09 14:23",
  },
  {
    id: "2",
    fullName: "RS Cipto Mangunkusumo",
    email: "admin.rscm@hospital.id",
    status: "Active",
    totalAnalyses: 487,
    lastAnalysis: "2025-11-09 11:45",
  },
  {
    id: "3",
    fullName: "RS Harapan Kita",
    email: "admin.rsharapan@hospital.id",
    status: "Inactive",
    totalAnalyses: 156,
    lastAnalysis: "2025-10-28 09:12",
  },
  {
    id: "4",
    fullName: "RS Fatmawati",
    email: "admin.rsfatmawati@hospital.id",
    status: "Active",
    totalAnalyses: 218,
    lastAnalysis: "2025-11-08 16:30",
  },
  {
    id: "5",
    fullName: "RSUD Surabaya",
    email: "admin.rssurabaya@hospital.id",
    status: "Active",
    totalAnalyses: 44,
    lastAnalysis: "2025-11-07 08:15",
  },
];

export function UsageStatisticsTable() {
  return (
    <Card className="shadow-lg rounded-xl border-0">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-t-xl border-b">
        <CardTitle className="text-blue-900">Usage Statistics per Admin RS</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b-2 border-gray-200 hover:bg-transparent">
                <TableHead className="text-gray-700">Full Name</TableHead>
                <TableHead className="text-gray-700">Email</TableHead>
                <TableHead className="text-gray-700">Status</TableHead>
                <TableHead className="text-gray-700">Total Analyses</TableHead>
                <TableHead className="text-gray-700">Last Analysis</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockStats.map((stat) => (
                <TableRow key={stat.id} className="hover:bg-blue-50/50 transition-colors border-b border-gray-100">
                  <TableCell className="text-gray-900">{stat.fullName}</TableCell>
                  <TableCell className="text-gray-700">{stat.email}</TableCell>
                  <TableCell>
                    <Badge
                      variant={stat.status === "Active" ? "default" : "secondary"}
                      className={
                        stat.status === "Active"
                          ? "bg-green-100 text-green-800 hover:bg-green-100 border-green-200"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-100 border-gray-200"
                      }
                    >
                      {stat.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <span className="text-blue-600">{stat.totalAnalyses}</span>
                  </TableCell>
                  <TableCell className="text-gray-700">{stat.lastAnalysis}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
