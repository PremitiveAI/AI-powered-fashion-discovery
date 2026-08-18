import Link from "next/link";
import StatusBadge from "./StatusBadge";
import { Employee } from "@/app/lib/types";

export default function EmployeeRow({ employee }: { employee: Employee }) {
  const completed = Object.values(employee.documents).every(Boolean);

  return (
    <Link
      href={`/employees/${employee.id}`}
      className="block bg-white rounded-xl p-4 shadow hover:bg-gray-100 transition"
    >
      <div className="flex justify-between items-center">
        <div>
          <p className="font-semibold text-gray-800">{employee.name}</p>
          <p className="text-sm text-gray-500">{employee.id}</p>
        </div>
        <StatusBadge completed={completed} />
      </div>
    </Link>
  );
}
