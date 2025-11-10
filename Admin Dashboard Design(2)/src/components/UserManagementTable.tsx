import { Badge } from "./ui/badge";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "./ui/alert-dialog";
import { toast } from "sonner@2.0.3";
import { Ban, Clock, Trash2 } from "lucide-react";

interface User {
  id: string;
  email: string;
  fullName: string;
  status: "Active" | "Inactive";
  activeUntil: string;
  createdAt: string;
}

const mockUsers: User[] = [
  {
    id: "1",
    email: "admin.rsudjakarta@hospital.id",
    fullName: "RSUD Jakarta Pusat",
    status: "Active",
    activeUntil: "2025-12-31",
    createdAt: "2024-01-15",
  },
  {
    id: "2",
    email: "admin.rscm@hospital.id",
    fullName: "RS Cipto Mangunkusumo",
    status: "Active",
    activeUntil: "2025-11-30",
    createdAt: "2024-02-20",
  },
  {
    id: "3",
    email: "admin.rsharapan@hospital.id",
    fullName: "RS Harapan Kita",
    status: "Inactive",
    activeUntil: "2025-06-15",
    createdAt: "2023-12-10",
  },
  {
    id: "4",
    email: "admin.rsfatmawati@hospital.id",
    fullName: "RS Fatmawati",
    status: "Active",
    activeUntil: "2026-01-31",
    createdAt: "2024-03-05",
  },
  {
    id: "5",
    email: "admin.rssurabaya@hospital.id",
    fullName: "RSUD Surabaya",
    status: "Active",
    activeUntil: "2025-10-20",
    createdAt: "2024-01-25",
  },
];

export function UserManagementTable() {
  const handleDeactivate = (userName: string) => {
    toast.success(`${userName} has been deactivated`);
  };

  const handleExtend = (userName: string) => {
    toast.success(`License extended for ${userName}`);
  };

  const handleDelete = (userName: string) => {
    toast.error(`${userName} has been deleted`);
  };

  return (
    <Card className="shadow-lg rounded-xl border-0">
      <CardHeader className="bg-gradient-to-r from-blue-50 to-blue-100 rounded-t-xl border-b">
        <CardTitle className="text-blue-900">Admin RS Accounts</CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow className="border-b-2 border-gray-200 hover:bg-transparent">
                <TableHead className="text-gray-700">Email</TableHead>
                <TableHead className="text-gray-700">Full Name</TableHead>
                <TableHead className="text-gray-700">Status</TableHead>
                <TableHead className="text-gray-700">Active Until</TableHead>
                <TableHead className="text-gray-700">Created At</TableHead>
                <TableHead className="text-right text-gray-700">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {mockUsers.map((user) => (
                <TableRow key={user.id} className="hover:bg-blue-50/50 transition-colors border-b border-gray-100">
                  <TableCell className="text-gray-700">{user.email}</TableCell>
                  <TableCell className="text-gray-900">{user.fullName}</TableCell>
                  <TableCell>
                    <Badge
                      variant={user.status === "Active" ? "default" : "secondary"}
                      className={
                        user.status === "Active"
                          ? "bg-green-100 text-green-800 hover:bg-green-100 border-green-200"
                          : "bg-gray-100 text-gray-600 hover:bg-gray-100 border-gray-200"
                      }
                    >
                      {user.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-gray-700">{user.activeUntil}</TableCell>
                  <TableCell className="text-gray-700">{user.createdAt}</TableCell>
                  <TableCell>
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        className="bg-white text-red-600 hover:bg-red-600 hover:text-white border-red-300 hover:border-red-600 shadow-sm transition-all"
                        onClick={() => handleDeactivate(user.fullName)}
                      >
                        <Ban className="h-3.5 w-3.5 mr-1.5" />
                        Deactivate
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="bg-white text-teal-600 hover:bg-teal-600 hover:text-white border-teal-300 hover:border-teal-600 shadow-sm transition-all"
                        onClick={() => handleExtend(user.fullName)}
                      >
                        <Clock className="h-3.5 w-3.5 mr-1.5" />
                        Extend
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="outline"
                            size="sm"
                            className="bg-white text-red-700 hover:bg-red-700 hover:text-white border-red-400 hover:border-red-700 shadow-sm transition-all"
                          >
                            <Trash2 className="h-3.5 w-3.5 mr-1.5" />
                            Delete
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
                            <AlertDialogDescription>
                              This action cannot be undone. This will permanently delete{" "}
                              <span className="text-red-600">{user.fullName}</span> account.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => handleDelete(user.fullName)}
                              className="bg-red-600 hover:bg-red-700"
                            >
                              Delete
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
