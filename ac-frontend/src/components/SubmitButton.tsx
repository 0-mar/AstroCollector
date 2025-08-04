export default function SubmitButton(pluginQuery) {
    if (pluginQuery.isPending) {
        return <p>Loading plugins...</p>
    }

    if (pluginQuery.isError) {
        return <p>Failed to load plugins: {pluginQuery.error.message}</p>
    }

    return (
        <button type="submit">Search</button>
    )
}
