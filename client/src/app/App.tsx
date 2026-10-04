import { lazy, Suspense, useEffect } from "react";
import { createBrowserRouter, RouterProvider } from "react-router";
import { warmUp } from "@/runtime/python";
import { useSettings } from "@/store/settings";
import { Layout } from "./Layout";
import { HomePage } from "@/features/home/HomePage";
import { ProblemsPage } from "@/features/problems/ProblemsPage";
import { NotFound } from "./NotFound";

// Heavy routes (editor, visualizer) are split out of the initial bundle.
const WorkspacePage = lazy(() => import("@/features/workspace/WorkspacePage"));
const PatternsPage = lazy(() => import("@/features/patterns/PatternsPage"));
const PatternPage = lazy(() => import("@/features/patterns/PatternPage"));
const ReviewPage = lazy(() => import("@/features/study/ReviewPage"));
const StatsPage = lazy(() => import("@/features/study/StatsPage"));
const PlaygroundPage = lazy(() => import("@/features/playground/PlaygroundPage"));

function Loading() {
  return (
    <div className="flex h-full items-center justify-center p-10">
      <div className="h-1 w-40 overflow-hidden rounded-full bg-elev-2">
        <div className="skeleton h-full w-full" />
      </div>
    </div>
  );
}

const lazyRoute = (node: React.ReactNode) => <Suspense fallback={<Loading />}>{node}</Suspense>;

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    errorElement: <NotFound crashed />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "problems", element: <ProblemsPage /> },
      { path: "problems/:id", element: lazyRoute(<WorkspacePage />) },
      { path: "patterns", element: lazyRoute(<PatternsPage />) },
      { path: "patterns/:id", element: lazyRoute(<PatternPage />) },
      { path: "review", element: lazyRoute(<ReviewPage />) },
      { path: "stats", element: lazyRoute(<StatsPage />) },
      { path: "playground", element: lazyRoute(<PlaygroundPage />) },
      { path: "*", element: <NotFound /> },
    ],
  },
]);

export function App() {
  useEffect(() => {
    warmUp();
    useSettings.persist.rehydrate();
  }, []);
  return <RouterProvider router={router} />;
}
