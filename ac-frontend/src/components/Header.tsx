import {Link} from '@tanstack/react-router'
import ProtectedContent from "@/components/auth/ProtectedContent.tsx";
import {useAuth} from "@/features/auth/useAuth.ts";
import {useLogout} from "@/features/auth/useLogout.ts";
import {UserRoleEnum} from "@/features/auth/types.ts";

export default function Header() {
    const auth = useAuth()
    const logout = useLogout()

    return (
        <header className="sticky top-0 z-50 p-2 flex gap-2 bg-white/90 backdrop-blur border-b text-black">
            <nav className="flex flex-row w-full items-end">
                <div className="px-2 py-2 font-medium text-xl">
                    <Link to="/" activeOptions={{ exact: true }} activeProps={{
                        className: "font-extrabold underline",
                    }}>AstroCollector</Link>
                </div>
                <div className="px-2 py-2 font-medium">
                    <Link to="/catalogs" activeProps={{
                        className: "font-extrabold underline",
                    }}>Supported catalogs</Link>
                </div>
                <div className="px-2 py-2 font-medium" >
                    <Link to="/about" activeProps={{
                        className: "font-extrabold underline",
                    }}>About</Link>
                </div>
                <ProtectedContent permittedRoles={[UserRoleEnum.SUPER_ADMIN]}>
                    <div className="px-2 py-2 font-medium">
                        <Link to="/admin/catalogManagement" activeProps={{
                            className: "font-extrabold underline",
                        }}>Catalog management</Link>
                    </div>
                </ ProtectedContent>
                {
                !auth?.isAuthenticated ?
                    (<div className="text-white bg-blue-700 hover:bg-blue-800 px-4 py-2 rounded ml-auto">
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
