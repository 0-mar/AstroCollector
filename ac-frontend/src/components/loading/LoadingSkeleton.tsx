import {Skeleton} from "@/../components/ui/skeleton.tsx";

const LoadingSkeleton = ({text}: {text: string}) => {
    return (
        <div className="flex items-center space-x-4">
            <Skeleton className="h-8 w-8 rounded-full" />
            <div className="space-y-2">
                <Skeleton className="h-4 w-[200px]" />
                <p className="text-sm text-muted-foreground animate-pulse">
                    {text}
                </p>
            </div>
        </div>
    )
}
export default LoadingSkeleton
