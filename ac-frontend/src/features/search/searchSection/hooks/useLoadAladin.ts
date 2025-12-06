import {useEffect, useState} from "react";
import {ALADIN_SCRIPT_URL} from "@/features/search/searchSection/constants.ts";

export const useLoadAladin = () => {
    const [isAladinLoaded, setAladinLoaded] = useState(false);

    useEffect(() => {
        const scriptTag = document.createElement('script');
        scriptTag.src = ALADIN_SCRIPT_URL;
        scriptTag.async = true;
        scriptTag.onload = () => setAladinLoaded(true);
        document.body.appendChild(scriptTag);

        return () => {
            document.body.removeChild(scriptTag);
        }
    }, []);

    return isAladinLoaded;
};
