import { Refine, ErrorComponent } from "@refinedev/core";
import { DevtoolsPanel, DevtoolsProvider } from "@refinedev/devtools";
import { RefineKbar, RefineKbarProvider } from "@refinedev/kbar";

import { BrowserRouter, Route, Routes, Outlet } from "react-router";
import routerProvider, {
  NavigateToResource,
  UnsavedChangesNotifier,
  DocumentTitleHandler,
} from "@refinedev/react-router";
import { Layout } from "./components/layout";
import "./App.css";
import { dataProvider } from "./providers/data";
import { ThemeProvider } from "./providers/theme";
import { DocTypeList, DocTypeEdit } from "./pages/doctypes";
import { initFieldComponentRegistry } from "./registry";

// Initialize field component registry on app load
initFieldComponentRegistry();

function App() {
  return (
    <ThemeProvider>
      <BrowserRouter basename="/studio/ui">
        <RefineKbarProvider>
          <DevtoolsProvider>
            <Refine
              dataProvider={dataProvider}
              routerProvider={routerProvider}
              resources={[
                {
                  name: "doctypes",
                  list: "/doctypes",
                  create: "/doctypes/create",
                  edit: "/doctypes/edit/:id",
                  meta: {
                    label: "DocTypes",
                    icon: "📄",
                  },
                },
              ]}
              options={{
                syncWithLocation: true,
                warnWhenUnsavedChanges: true,
                projectId: "framework-m-studio",
              }}
            >
              <Routes>
                <Route
                  element={
                    <Layout>
                      <Outlet />
                    </Layout>
                  }
                >
                  <Route index element={<NavigateToResource resource="doctypes" />} />
                  <Route path="/doctypes">
                    <Route index element={<DocTypeList />} />
                    <Route path="create" element={<DocTypeEdit />} />
                    <Route path="edit/:id" element={<DocTypeEdit />} />
                  </Route>
                  <Route path="*" element={<ErrorComponent />} />
                </Route>
              </Routes>
              <RefineKbar />
              <UnsavedChangesNotifier />
              <DocumentTitleHandler />
            </Refine>
            <DevtoolsPanel />
          </DevtoolsProvider>
        </RefineKbarProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;

