import {Link} from '@tanstack/react-router'
import ProtectedContent from "@/features/common/auth/components/ProtectedContent.tsx";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {useLogout} from "@/features/common/auth/hooks/useLogout.ts";
import {UserRoleEnum} from "@/features/common/auth/types.ts";
import {useState} from "react";

export default function Header() {
    const auth = useAuth()
    const logout = useLogout()
    const [open, setOpen] = useState<boolean>(false)

    const activeClass =
        "block py-2 px-3 text-white bg-blue-700 rounded-sm md:bg-transparent md:text-blue-700 md:p-0";
    const inactiveClass =
        "block py-2 px-3 text-gray-900 rounded-sm hover:bg-gray-100 md:hover:bg-transparent md:border-0 md:hover:text-blue-700 md:p-0";


    return (
        <nav className="bg-white border-gray-600 border-b-2 rounded-b-lg sticky top-0 z-10">
            <div className="flex flex-wrap items-center justify-between p-4">
                <Link
                    to="/"
                    activeOptions={{exact: true}}
                    className="flex items-center space-x-3 rtl:space-x-reverse"
                    onClick={() => setOpen(false)}
                >
                    <img className={"w-10 h-10"}
                        src="/planet.svg"
                        alt="planet logo" />
                    <span
                        className="self-center text-2xl font-semibold whitespace-nowrap text-transparent bg-clip-text bg-gradient-to-r to-black from-amber-400">
                        AstroCollector
                    </span>
                </Link>
                <button onClick={() => setOpen(o => !o)}
                        className="inline-flex items-center p-2 w-10 h-10 justify-center text-sm text-gray-500 rounded-lg md:hidden hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-200"
                        aria-controls="navbar-default" aria-expanded={open}>
                    <span className="sr-only">Open main menu</span>
                    <svg className="w-5 h-5" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none"
                         viewBox="0 0 17 14">
                        <path stroke="currentColor" d="M1 1h15M1 7h15M1 13h15"/>
                    </svg>
                </button>
                <div className={`${open ? "block" : "hidden"} w-full md:ml-auto md:block md:w-auto`} id="navbar-default">
                    <ul className="font-medium flex flex-col p-4 md:p-0 mt-4 border border-gray-100 rounded-lg bg-gray-100 md:flex md:items-center md:flex-row md:space-x-8 rtl:space-x-reverse md:mt-0 md:border-0 md:bg-white">
                        <li>
                            <Link
                                to="/catalogs"
                                activeProps={{ className: activeClass }}
                                inactiveProps={{ className: inactiveClass }}
                                onClick={() => setOpen(false)}
                            >
                                Supported catalogs
                            </Link>
                        </li>
                        <li>
                            <Link
                                to="/about"
                                className={"align-middle"}
                                activeProps={{ className: activeClass }}
                                inactiveProps={{ className: inactiveClass }}
                                onClick={() => setOpen(false)}
                            >
                                About
                            </Link>
                        </li>
                        <ProtectedContent permittedRoles={[UserRoleEnum.SUPER_ADMIN]}>
                            <li>
                                <Link
                                    to="/admin/catalogManagement"
                                    activeProps={{ className: activeClass }}
                                    inactiveProps={{ className: inactiveClass }}
                                    onClick={() => setOpen(false)}
                                >
                                    Catalog management
                                </Link>
                            </li>
                        </ ProtectedContent>
                        {
                            !auth?.isAuthenticated ?
                                (<li>
                                    <Link
                                        to="/login"
                                        activeProps={{ className: activeClass }}
                                        inactiveProps={{ className: inactiveClass }}
                                        onClick={() => setOpen(false)}
                                        search={{redirect: "/"}}
                                    >
                                        Login
                                    </Link>
                                </li>)
                                : (
                                    <li>
                                        <div className="md:hidden min-h-5"></div>
                                        <button
                                            className="block py-2 px-3 w-full rounded-sm
                 bg-red-600 text-white hover:bg-red-700
                 md:mx-0 md:w-auto"
                                            onClick={async () => await logout.mutateAsync()}
                                        >
                                            Sign Out
                                        </button>
                                    </li>
                                )
                        }

                    </ul>
                </div>
            </div>
        </nav>

    )
}
