import { useEffect } from "react";

const SUFFIX = "Paper-Mind";

/** Give each screen its own browser-tab title, e.g. "Library — Paper-Mind". */
export function useDocumentTitle(title) {
  useEffect(() => {
    const previous = document.title;
    document.title = title ? title + " — " + SUFFIX : SUFFIX;
    return () => {
      document.title = previous;
    };
  }, [title]);
}
