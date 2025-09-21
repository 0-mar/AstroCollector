// import { createFileRoute } from "@tanstack/react-router"
// import {createFileRouteWithRoleProtection} from "@/features/routing/roleRoute.ts";
// import {UserRoleEnum} from "@/features/auth/types.ts";
//
// // export const Route = createFileRoute('/_superAdmin/admin/catalogManagement')({
// //     component: DashboardComponent,
// // })
//
// export const Route = createFileRouteWithRoleProtection('/catalogManagement')('/catalogManagement', [UserRoleEnum.SUPER_ADMIN], DashboardComponent)
//
// function DashboardComponent() {
//     const { auth } = Route.useRouteContext()
//
//     return (
//         <div className="p-6">
//             <div className="flex justify-between items-center mb-6">
//                 <h1 className="text-3xl font-bold">Dashboard</h1>
//                 <button
//                     className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
//                 >
//                     Sign Out
//                 </button>
//             </div>
//
//             <div className="bg-white p-6 rounded-lg shadow">
//                 <h2 className="text-xl font-semibold mb-2">Welcome back!</h2>
//                 <p className="text-gray-600">
//                     Hello, <strong>{auth.user?.username}</strong>! You are successfully
//                     authenticated.
//                 </p>
//                 <p className="text-sm text-gray-500 mt-2">Email: {auth.user?.email}</p>
//             </div>
//         </div>
//     )
// }
