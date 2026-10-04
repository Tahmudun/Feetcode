import { Link } from "react-router";
import { Button } from "@/ui/primitives";

export function NotFound({ crashed = false }: { crashed?: boolean }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 px-6 text-center">
      <div className="font-display text-6xl font-extrabold text-faint">{crashed ? "¹" : "404"}</div>
      <p className="max-w-md text-muted">
        {crashed
          ? "Something broke while rendering this page. Reload to try again - your code and progress are saved locally."
          : "That page doesn't exist. Even our fuzzer couldn't find it."}
      </p>
      <Link to="/problems">
        <Button variant="primary">Back to problems</Button>
      </Link>
    </div>
  );
}
