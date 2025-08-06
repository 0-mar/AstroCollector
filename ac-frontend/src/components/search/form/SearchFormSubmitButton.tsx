import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import LoadingError from "@/components/loading/LoadingError.tsx";
import { Button } from "@/../components/ui/button"

const SearchFormSubmitButton = ({pluginQuery}) => {
    if (pluginQuery.isPending) {
        return <LoadingSkeleton text={"Loading catalogs..."} />
    }

    if (pluginQuery.isError) {
        return <LoadingError title={"Failed to load catalogs"} description={pluginQuery.error.message} />
    }

    return (
        <Button>Search</Button>
    )
}

export default SearchFormSubmitButton;
