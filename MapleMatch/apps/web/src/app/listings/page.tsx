"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useListings } from "@/hooks/useApi";
import type { Listing } from "@/lib/api";
import { MapPin, DollarSign, Bed, Accessibility } from "lucide-react";

const PROVINCES = [
  "AB",
  "BC",
  "MB",
  "NB",
  "NL",
  "NS",
  "NT",
  "NU",
  "ON",
  "PE",
  "QC",
  "SK",
  "YT",
] as const;

export default function ListingsPage() {
  const { t } = useTranslation();
  const [filters, setFilters] = useState({
    city: "",
    province: "any",
    max_rent: "",
    bedrooms: "",
    is_accessible: "any",
    is_rgi: "any",
  });

  const params = new URLSearchParams();
  if (filters.city) params.set("city", filters.city);
  if (filters.province && filters.province !== "any") params.set("province", filters.province);
  if (filters.max_rent) params.set("max_rent", filters.max_rent);
  if (filters.bedrooms) params.set("bedrooms", filters.bedrooms);
  if (filters.is_accessible && filters.is_accessible !== "any") params.set("is_accessible", filters.is_accessible);
  if (filters.is_rgi && filters.is_rgi !== "any") params.set("is_rgi", filters.is_rgi);

  const { data: listings, isLoading, isError } = useListings(params);

  return (
    <main className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">{t("listings.title")}</h1>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg">{t("listings.filters")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-1">
              <Label htmlFor="f-city">{t("listings.city")}</Label>
              <Input
                id="f-city"
                placeholder="Toronto"
                value={filters.city}
                onChange={(e) =>
                  setFilters((f) => ({ ...f, city: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="f-province">{t("listings.province")}</Label>
              <Select
                value={filters.province}
                onValueChange={(v) =>
                  setFilters((f) => ({ ...f, province: v }))
                }
              >
                <SelectTrigger id="f-province">
                  <SelectValue placeholder={t("listings.allProvinces")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">{t("listings.allProvinces")}</SelectItem>
                  {PROVINCES.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="f-rent">{t("listings.maxRent")}</Label>
              <Input
                id="f-rent"
                type="number"
                min={0}
                placeholder="2000"
                value={filters.max_rent}
                onChange={(e) =>
                  setFilters((f) => ({ ...f, max_rent: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="f-bed">{t("listings.bedrooms")}</Label>
              <Input
                id="f-bed"
                type="number"
                min={0}
                placeholder="2"
                value={filters.bedrooms}
                onChange={(e) =>
                  setFilters((f) => ({ ...f, bedrooms: e.target.value }))
                }
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="f-accessible">{t("listings.accessible")}</Label>
              <Select
                value={filters.is_accessible}
                onValueChange={(v) =>
                  setFilters((f) => ({ ...f, is_accessible: v }))
                }
              >
                <SelectTrigger id="f-accessible">
                  <SelectValue placeholder={t("listings.any")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">{t("listings.any")}</SelectItem>
                  <SelectItem value="true">{t("listings.yes")}</SelectItem>
                  <SelectItem value="false">{t("listings.no")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="f-rgi">{t("listings.rgi")}</Label>
              <Select
                value={filters.is_rgi}
                onValueChange={(v) =>
                  setFilters((f) => ({ ...f, is_rgi: v }))
                }
              >
                <SelectTrigger id="f-rgi">
                  <SelectValue placeholder={t("listings.any")} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="any">{t("listings.any")}</SelectItem>
                  <SelectItem value="true">{t("listings.yes")}</SelectItem>
                  <SelectItem value="false">{t("listings.no")}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <Button
            variant="outline"
            className="mt-4"
            onClick={() =>
              setFilters({
                city: "",
                province: "any",
                max_rent: "",
                bedrooms: "",
                is_accessible: "any",
                is_rgi: "any",
              })
            }
          >
            {t("listings.clearFilters")}
          </Button>
        </CardContent>
      </Card>

      {/* Results */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48 rounded-lg" />
          ))}
        </div>
      )}

      {isError && (
        <p className="text-destructive" role="alert">
          {t("common.error")}
        </p>
      )}

      {listings && listings.length === 0 && (
        <p className="text-muted-foreground text-center py-12">
          {t("listings.noResults")}
        </p>
      )}

      {listings && listings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {listings.map((listing) => (
            <ListingCard key={listing.id} listing={listing} />
          ))}
        </div>
      )}
    </main>
  );
}

function ListingCard({ listing }: { listing: Listing }) {
  const { t } = useTranslation();
  return (
    <Card className="flex flex-col">
      <CardHeader className="pb-3">
        <CardTitle className="text-base leading-snug">
          {listing.title}
        </CardTitle>
        <CardDescription className="flex items-center gap-1">
          <MapPin className="size-3.5" />
          {listing.city}, {listing.province}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex-1 space-y-2 text-sm">
        <div className="flex items-center gap-1.5">
          <DollarSign className="size-3.5 text-muted-foreground" />
          <span className="font-medium">
            ${listing.rent_amount.toLocaleString()}/mo
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Bed className="size-3.5 text-muted-foreground" />
          <span>
            {listing.bedrooms} {t("listings.bed")} · {listing.bathrooms}{" "}
            {t("listings.bath")}
          </span>
        </div>
        <div className="flex flex-wrap gap-1 pt-1">
          {listing.is_rgi && (
            <Badge variant="secondary">{t("listings.rgi")}</Badge>
          )}
          {listing.is_accessible && (
            <Badge variant="secondary">
              <Accessibility className="size-3 mr-0.5" />
              {t("listings.accessible")}
            </Badge>
          )}
          {listing.status !== "active" && (
            <Badge variant="outline">{listing.status}</Badge>
          )}
        </div>
        {listing.description && (
          <p className="text-muted-foreground line-clamp-2 pt-1">
            {listing.description}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
