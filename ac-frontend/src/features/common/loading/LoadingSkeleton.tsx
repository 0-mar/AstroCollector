import LoadingWheel from "@/features/common/loading/LoadingWheel.tsx";

const LoadingSkeleton = ({text}: {text: string}) => {
    return (
        <div className="flex items-center space-x-4">
            <LoadingWheel height={'3rem'} width={'3rem'}/>
            <p className="text-sm text-muted-foreground animate-pulse">
                {text}
            </p>
        </div>
    )
}
export default LoadingSkeleton
