import {createFileRoute, Outlet} from '@tanstack/react-router'

export const Route = createFileRoute('/app')({
    component: LayoutComponent,
})

function LayoutComponent() {
    return (
        <Outlet />
    )
}
