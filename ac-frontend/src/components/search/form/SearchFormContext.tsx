import React, {createContext, useMemo, useState} from "react"
import type {SearchFormValues} from "@/features/search/searchSection/schemas.ts";

type SearchFormCtx = {
    searchValues: SearchFormValues; setSearchValues: React.Dispatch<React.SetStateAction<SearchValues>>;
};

export const SearchFormContext = createContext<SearchFormCtx | null>(null)

export const SearchFormProvider = ({ children }) => {
    const [searchValues, setSearchValues] = useState<SearchValues>({})

    const value = useMemo(
        () => ({
            searchValues,
            setSearchValues,
        }),
        [searchValues]
    );

    return (
        <SearchFormContext.Provider value={value}>
            {children}
        </SearchFormContext.Provider>
    );
};
