import {Link} from '@tanstack/react-router'
import ProtectedContent from "@/components/auth/ProtectedContent.tsx";
import {useAuth} from "@/features/auth/useAuth.ts";
import {useLogout} from "@/features/auth/useLogout.ts";
import {UserRoleEnum} from "@/features/auth/types.ts";

export default function Header() {
    const auth = useAuth()
    const logout = useLogout()


    return (
        <header className="p-2 flex gap-2 bg-white text-black justify-between">
            <nav className="flex flex-row w-full">
                <div className="px-2 py-2 font-bold">
                    <Link to="/">AstroCollector</Link>
                </div>
                <div className="px-2 py-2 font-bold">
                    <Link to="/catalogs">Supported catalogs</Link>
                </div>
                <div className="px-2 py-2 font-bold">
                    <Link to="/about">About</Link>
                </div>
                <ProtectedContent permittedRoles={[UserRoleEnum.SUPER_ADMIN]}>
                    <div className="px-2 py-2 font-bold">
                        <Link to="/admin/catalogManagement">Catalog management</Link>
                    </div>
                </ ProtectedContent>
                {
                !auth?.isAuthenticated ?
                    (<div className="bg-blue-400 text-black px-4 py-2 rounded hover:bg-blue-500 ml-auto">
                        <Link to="/login" search={{redirect: "/"}}>Login</Link>
                    </div>)
                : (
                    <button
                    className="bg-red-600 text-black px-4 py-2 rounded hover:bg-red-700 ml-auto"
                    onClick={async () => await logout.mutateAsync()}
                    >
                    Sign Out
                    </button>
                    )
                }

            </nav>
        </header>
    )
}
