/**
 * useFields Hook
 *
 * Custom hook for fetching and managing field data
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  listFields,
  getField,
  createField,
  updateField,
  deleteField,
  getFieldStats,
  toFieldData,
  type FieldCreate,
  type FieldUpdate,
  type FieldDetail,
  type FieldStats,
} from '@/services/fields';
import type { FieldData } from '@/types';

/**
 * Query keys for field-related queries
 */
export const fieldKeys = {
  all: ['fields'] as const,
  lists: () => [...fieldKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...fieldKeys.lists(), filters] as const,
  details: () => [...fieldKeys.all, 'detail'] as const,
  detail: (id: string) => [...fieldKeys.details(), id] as const,
  stats: () => [...fieldKeys.all, 'stats'] as const,
};

/**
 * Hook to fetch paginated list of fields
 */
export function useFields(
  params: {
    skip?: number;
    limit?: number;
    district?: string;
    crop_type?: string;
  } = {}
) {
  return useQuery({
    queryKey: fieldKeys.list(params),
    queryFn: () => listFields(params),
    select: (data) => ({
      total: data.total,
      skip: data.skip,
      limit: data.limit,
      items: data.items.map(toFieldData),
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

/**
 * Hook to fetch a single field by ID
 */
export function useField(fieldId: string | null) {
  return useQuery({
    queryKey: fieldKeys.detail(fieldId || ''),
    queryFn: () => getField(fieldId!),
    enabled: !!fieldId,
    select: toFieldData,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook to fetch field statistics
 */
export function useFieldStats() {
  return useQuery({
    queryKey: fieldKeys.stats(),
    queryFn: getFieldStats,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to create a new field
 */
export function useCreateField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: FieldCreate) => createField(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fieldKeys.lists() });
      toast.success('Field created successfully');
    },
    onError: () => {
      toast.error('Failed to create field');
    },
  });
}

/**
 * Hook to update a field
 */
export function useUpdateField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ fieldId, data }: { fieldId: string; data: FieldUpdate }) =>
      updateField(fieldId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: fieldKeys.lists() });
      queryClient.invalidateQueries({ queryKey: fieldKeys.detail(variables.fieldId) });
      toast.success('Field updated successfully');
    },
    onError: () => {
      toast.error('Failed to update field');
    },
  });
}

/**
 * Hook to delete a field
 */
export function useDeleteField() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (fieldId: string) => deleteField(fieldId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fieldKeys.lists() });
      toast.success('Field deleted successfully');
    },
    onError: () => {
      toast.error('Failed to delete field');
    },
  });
}

/**
 * Hook to get all fields (for map display)
 */
export function useAllFields() {
  return useQuery({
    queryKey: fieldKeys.list({}),
    queryFn: () => listFields({ limit: 1000 }),
    select: (data) => data.items.map(toFieldData),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Hook to get fields by district
 */
export function useFieldsByDistrict(districtId: string | null) {
  const params = districtId ? { district: districtId } : {};
  return useQuery({
    queryKey: fieldKeys.list(params),
    queryFn: () => listFields(params),
    enabled: !!districtId,
    select: (data) => data.items.map(toFieldData),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Combined hook for fields map display
 */
export function useFieldsMap() {
  const { data: fields, isLoading, error } = useAllFields();
  const { data: stats } = useFieldStats();

  return {
    fields: fields || [],
    stats,
    isLoading,
    error,
  };
}
