import {createFileRoute, Outlet} from '@tanstack/react-router'

export const Route = createFileRoute('/app')({
    component: LayoutComponent,
})

function LayoutComponent() {
    return (
        <div className="grid grid-cols-5 grid-rows-5 gap-6">
            <div className="col-span-5 bg-slate-900">This is layout header</div>
            <div className="col-span-5 row-span-4 row-start-2 bg-slate-100">
                <Outlet />
            </div>
        </div>

    )
}
