import { Link, useLocation } from "react-router-dom"
import { ClipboardListIcon, LayoutDashboardIcon, MapIcon, Rows3Icon } from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"

const LINKS = [
  { to: "/", label: "Overview", icon: LayoutDashboardIcon },
  { to: "/transactions", label: "Transactions", icon: Rows3Icon },
  { to: "/transactions?review_only=1", label: "Review queue", icon: ClipboardListIcon },
  { to: "/mappings", label: "Mappings", icon: MapIcon },
] as const

export function AppSidebar() {
  const location = useLocation()

  return (
    <Sidebar>
      <SidebarHeader>
        <div className="flex flex-col gap-1 px-2 py-2">
          <p className="text-sm font-medium">Expenditure review</p>
          <p className="text-xs text-muted-foreground">SHA / SRHR prototype</p>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Analyst</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {LINKS.map((item) => {
                const search = item.to.includes("?") ? item.to.slice(item.to.indexOf("?")) : ""
                const pathname = item.to.split("?")[0]
                const isActive =
                  location.pathname === pathname &&
                  (search ? location.search.includes("review_only=1") : !location.search.includes("review_only=1"))
                return (
                  <SidebarMenuItem key={item.to}>
                    <SidebarMenuButton
                      isActive={isActive}
                      render={<Link to={item.to} />}
                    >
                      <item.icon data-icon="inline-start" />
                      {item.label}
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                )
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
